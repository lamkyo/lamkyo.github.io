**🛠️  Bản tóm tắt giải pháp cho issue `ext-gh-Nudge-Pay-nudge-server-52`**  

> **Mục tiêu:** Ngăn người dùng không‑owner truy cập `GET /v1/payment-requests/:id` bằng cách kiểm tra `receiverUserId` trong quá trình truy vấn và trả về **404 – PAYMENT_REQUEST_NOT_FOUND**.  

---

## 1. ROOT CAUSE & TECHNICAL ANALYSIS  

| Thành phần | Vấn đề | Hậu quả |
|------------|--------|---------|
| `PaymentRequestsController.findById` | Nhận `_currentUser` nhưng **không truyền** vào service. | Người gọi có thể truyền bất kỳ UUID nào và nhận dữ liệu của người khác. |
| `PaymentRequestsService.findById(id)` | Chỉ gọi repository với **filter `{ id }`**. | Không có ràng buộc `receiverUserId`. |
| `PaymentRequestsRepository.findById(id)` | Truy vấn **WHERE id = $1**. | Trả về bản ghi bất kể người sở hữu. |
| `@ApiOperation` | Mô tả “authenticated user must be the owner”, nhưng **code không thực thi**. | Lỗi bảo mật (information disclosure). |

**Nguyên nhân gốc**: Thiếu **ownership guard** – không có cách nào truyền `receiverUserId` (được ánh xạ từ `supabaseId` của người dùng hiện tại) tới tầng repository. Do đó, bất kỳ người dùng nào có UUID hợp lệ đều có thể đọc thông tin nhạy cảm của người khác.

**Yêu cầu kiến trúc**:  
1. **Resolver**: Từ `_currentUser.supabaseId` (hoặc `userId` tùy model) lấy `internalUserId` thông qua `UsersService.getUserBySupabaseId`.  
2. **Service**: Nhận thêm tham số `ownerId` và truyền xuống repository.  
3. **Repository**: Thêm điều kiện `receiverUserId = $2` (hoặc `ownerId`).  
4. **Controller**: Sử dụng `_currentUser` thực sự, không tắt eslint.  
5. **Error handling**: Khi không tìm thấy (cũng bao gồm “không phải của mình”) trả về `NotFoundException` với code `PAYMENT_REQUEST_NOT_FOUND`.  

---

## 2. SURGICAL CODE SOLUTION  

> **Giả định**:  
> - Dự án dùng **NestJS** + **TypeORM** (hoặc Prisma).  
> - `UsersService.getUserBySupabaseId(supabaseId)` trả về entity người dùng có trường `id` (internal).  
> - Các exception được định nghĩa trong `src/common/exceptions`.  

### 2.1. Controller (`src/payment-requests/payment-requests.controller.ts`)

```typescript
<pre><code>import {
  Controller,
  Get,
  Param,
  NotFoundException,
  UseGuards,
} from '@nestjs/common';
import { ApiOperation, ApiResponse } from '@nestjs/swagger';
import { CurrentUser } from '../auth/decorators/current-user.decorator';
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard';
import { PaymentRequestsService } from './payment-requests.service';
import { PAYMENT_REQUEST_NOT_FOUND } from '../common/constants/error-codes';

@Controller('v1/payment-requests')
@UseGuards(JwtAuthGuard)
export class PaymentRequestsController {
  constructor(private readonly paymentRequestsService: PaymentRequestsService) {}

  @Get(':id')
  @ApiOperation({
    summary:
      'Get a payment request. The authenticated user must be the owner (receiverUserId).',
  })
  @ApiResponse({ status: 200, description: 'Payment request found.' })
  @ApiResponse({ status: 404, description: PAYMENT_REQUEST_NOT_FOUND })
  async findById(
    @Param('id') id: string,
    @CurrentUser() currentUser: any, // { supabaseId: string, ... }
  ) {
    const paymentRequest = await this.paymentRequestsService.findById(
      id,
      currentUser,
    );

    if (!paymentRequest) {
      // Không tiết lộ rằng bản ghi tồn tại nhưng không thuộc sở hữu
      throw new NotFoundException({
        code: PAYMENT_REQUEST_NOT_FOUND,
        message: 'Payment request not found',
      });
    }

    return paymentRequest;
  }
}
</code></pre>
```

### 2.2. Service (`src/payment-requests/payment-requests.service.ts`)

```typescript
<pre><code>import { Injectable, NotFoundException } from '@nestjs/common';
import { PaymentRequestsRepository } from './payment-requests.repository';
import { UsersService } from '../users/users.service';
import { PAYMENT_REQUEST_NOT_FOUND } from '../common/constants/error-codes';

@Injectable()
export class PaymentRequestsService {
  constructor(
    private readonly repo: PaymentRequestsRepository,
    private readonly usersService: UsersService,
  ) {}

  /**
   * Find a payment request by its public id **and** ensure it belongs to the
   * caller (receiverUserId).
   *
   * @param id            Public UUID of the payment request
   * @param currentUser   Object injected by @CurrentUser (contains supabaseId)
   * @returns             PaymentRequest entity or null
   */
  async findById(id: string, currentUser: any) {
    // Resolve internal user id from supabaseId (same logic used in PaymentsService.authorize)
    const internalUser = await this.usersService.getUserBySupabaseId(
      currentUser.supabaseId,
    );

    if (!internalUser) {
      // Nếu người dùng không tồn tại, treat as not‑found – will be caught by controller
      return null;
    }

    // Pass both id and ownerId to repository
    return this.repo.findById(id, internalUser.id);
  }
}
</code></pre>
```

### 2.3. Repository (`src/payment-requests/payment-requests.repository.ts`)

> **Nếu dùng TypeORM** (điều chỉnh cho Prisma nếu dự án dùng Prisma).

```typescript
<pre><code>import { EntityRepository, Repository } from 'typeorm';
import { PaymentRequest } from './entities/payment-request.entity';
import { Injectable } from '@nestjs/common';

@Injectable()
@EntityRepository(PaymentRequest)
export class PaymentRequestsRepository extends Repository<PaymentRequest> {
  /**
   * Find a payment request by id **and** receiverUserId.
   *
   * @param id          Public UUID
   * @param ownerId     Internal user id (receiverUserId)
   * @returns

⚡ <i>GPT OSS 120B (Groq LPU (Free) • 3.46s • $0.00)</i>