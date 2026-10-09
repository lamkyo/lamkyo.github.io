Chào bạn, đây là phân tích chi tiết và đề xuất giải pháp cho yêu cầu tư vấn (Consulting/Review) về việc di chuyển (migration) hệ thống WooCommerce Subscriptions kết hợp Stripe.

Lưu ý quan trọng: Đây là một yêu cầu **tư vấn kỹ thuật (Technical Review)** chứ không phải sửa một "bug" cụ thể trong code. Tuy nhiên, để đáp ứng cấu trúc 4 phần mà bạn yêu cầu, tôi sẽ chuyển đổi "Root Cause" thành **Rủi ro kiến trúc chính (Architectural Risks)**, "Code Solution" thành **Kịch bản kiểm tra & Cấu hình an toàn (Safety Check Script & Config)**, và "PR" thành **Báo cáo thẩm định (Audit Report)**.

Dưới đây là giải pháp chuẩn xác, chuyên nghiệp dành cho một kỹ sư cấp cao (Principal Engineer).

### 1. ROOT CAUSE & TECHNICAL ANALYSIS

**Vấn đề cốt lõi (The Core Risk):**
Khi di chuyển một hệ thống WooCommerce có tích hợp Stripe Subscriptions sang domain mới, rủi ro lớn nhất không nằm ở việc sao chép dữ liệu (DB sync), mà nằm ở **đồng bộ hóa trạng thái (State Synchronization)** giữa cơ sở dữ liệu cục bộ (Local DB) và API của Stripe.

Các rủi ro kỹ thuật cụ thể cần loại bỏ:
1.  **Webhook Race Condition (Xung đột điều khiển):** Nếu webhook của Stripe vẫn trỏ về domain cũ trong khi domain mới đã nhận yêu cầu thanh toán, hoặc ngược lại, sẽ dẫn đến tình trạng:
    *   *Duplicate Charge:* Cả hai domain đều xử lý sự kiện `invoice.payment_succeeded` và tạo đơn hàng mới.
    *   *Missed Renewal:* Sự kiện bị bỏ qua nếu secret key không khớp hoặc endpoint bị vô hiệu hóa tạm thời.
2.  **Mất liên kết Meta Data:** Các trường `_stripe_subscription_id`, `_stripe_customer_id` trong bảng `wp_postmeta` (của đơn hàng/khách hàng) là "chìa khóa" liên kết. Nếu quá trình sao chép DB không đảm bảo tính toàn vẹn (integrity) của các meta này, hoặc nếu plugin WooCommerce Subscriptions trên domain mới không nhận diện đúng trạng thái subscription từ Stripe, nó sẽ tạo ra các subscription "côi" (orphaned) hoặc cố gắng tạo subscription mới (double billing).
3.  **Plugin Activation Conflict:** Việc kích hoạt plugin WooCommerce Subscriptions và Stripe Gateway trên domain mới *trước* khi hoàn tất đồng bộ DB có thể kích hoạt các hook tự động (cron jobs) kiểm tra trạng thái subscription, dẫn đến việc gọi API Stripe và thay đổi trạng thái không mong muốn.

**Giải pháp kiến trúc (The Strategy):**
*   **Freeze & Sync:** Đóng băng các thay đổi dữ liệu trên domain cũ (Read-only mode nếu có thể, hoặc tạm dừng cron).
*   **Atomic Cutover:** Chuyển đổi webhook endpoint và kích hoạt domain mới phải diễn ra gần như đồng bộ (atomic) để giảm thiểu cửa sổ thời gian (time window) rủi ro.
*   **Verification Layer:** Sau khi cutover, cần một script kiểm tra chéo (cross-check) giữa DB cục bộ và API Stripe để đảm bảo mọi subscription đều khớp.

### 2. SURGICAL CODE SOLUTION

Đây là một script PHP (có thể chạy qua WP-CLI hoặc CLI) dùng để **thẩm định và xác minh** sự đồng bộ giữa DB WooCommerce và Stripe API sau khi migration. Script này không thay đổi dữ liệu mà chỉ kiểm tra và báo cáo, đảm bảo an toàn.

```php
<?php
/**
 * Stripe-WooCommerce Subscription Migration Validator
 * Usage: wp eval-file validate_stripe_migration.php --path=/tmp/validate_stripe_migration.php
 * Or run via CLI in WordPress environment.
 */

if (!defined('ABSPATH')) {
    die("Direct access not allowed.");
}

class StripeMigrationValidator {
    
    private $stripe_api_key;
    private $log = [];

    public function __construct() {
        // Lấy API Key từ WooCommerce Settings hoặc Constant
        $this->stripe_api_key = get_option('woocommerce_stripe_settings')['test_mode'] 
            ? get_option('woocommerce_stripe_settings')['test_secret_key']
            : get_option('woocommerce_stripe_settings')['secret_key'];

        if (empty($this->stripe_api_key)) {
            throw new Exception("Stripe Secret Key not found in WooCommerce settings.");
        }
        
        // Khởi tạo Stripe Client (Giả sử đã cài đặt stripe-php)
        \Stripe\Stripe::setApiKey($this->stripe_api_key);
    }

    public function run_validation() {
        echo "Starting Stripe-WooCommerce Migration Validation...\n";
        echo "Date: " . date('Y-m-d H:i:s') . "\n";
        echo str_repeat("-", 50) . "\n";

        $errors = 0;
        $warnings = 0;
        $total_checked = 0;

        // Lấy tất cả các đơn hàng có subscription
        $args = [
            'post_type' => 'shop_order',
            'meta_key' => '_stripe_subscription_id',
            'meta_value' => 'NOT EMPTY',
            'posts_per_page' => -1,
            'post_status' => 'any'
        ];

        $orders = get_posts($args);
        $total_checked = count($orders);
        echo "Total Orders with Stripe Subscriptions found: {$total_checked}\n";

        foreach ($orders as $order) {
            $order_id = $order->ID;
            $wc_order = wc_get_order($order_id);
            
            if (!$wc_order) continue;

            $stripe_sub_id = $wc_order->get_meta('_stripe_subscription_id');
            $stripe_customer_id = $wc_order->get_meta('_stripe_customer_id');
            $wc_sub_status = $wc_order->get_meta('_subscription_status'); // active, on-hold, etc.

            if (empty($stripe_sub_id)) {
                $this->log_error("Order #{$order_id}: Missing _stripe_subscription_id meta.");
                $errors++;
                continue;
            }

            try {
                // Gọi API Stripe để lấy trạng thái thực tế
                $stripe_sub = \Stripe\Subscription::retrieve($stripe_sub_id);
                
                // 1. Kiểm tra trạng thái đồng bộ
                if ($stripe_sub->status !== 'active' && $stripe_sub->status !== 'trialing') {
                    // Nếu Stripe đã hủy nhưng WC vẫn active -> Rủi ro cao
                    if ($wc_sub_status === 'active') {
                        $this->log_error("Order #{$order_id}: WC is 'active' but Stripe is '{$stripe_sub->status}'. Potential double billing or missed cancellation.");
                        $errors++;
                    }
                }

                // 2. Kiểm tra Customer ID
                if ($stripe_customer_id && $stripe_sub->customer !== $

⚡ <i>Qwen 3.8 27B (Groq LPU (Free) • 3.16s • $0.00)</i>