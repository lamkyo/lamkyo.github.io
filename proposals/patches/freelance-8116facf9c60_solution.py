Chào bạn, tôi là Antigravity.

Dựa trên dữ liệu hệ thống và mô tả công việc, đây là một bài toán **AI/ML Engineering** cụ thể liên quan đến **Vision-and-Language Navigation (VLN)** trên môi trường bay (Aerial). Bài toán yêu cầu xây dựng một module "Translator" (TGIT) để chuyển đổi các lệnh ngắn, mơ hồ (Weak commands) thành các lệnh chi tiết mà bộ điều hướng (Navigator) đóng băng (frozen) có thể hiểu và thực thi, dựa trên kết quả quỹ đạo (trajectory outcomes).

Dưới đây là giải pháp hoàn chỉnh, chuẩn sản xuất (production-ready).

### 1. ROOT CAUSE & TECHNICAL ANALYSIS

**Vấn đề cốt lõi (The Instruction Gap):**
Bộ điều hướng OpenFly được huấn luyện trên các lệnh chi tiết, bám sát quỹ đạo (trajectory-aligned). Tuy nhiên, người dùng thực tế đưa ra các lệnh ngắn, mang tính ý định (intent-driven). Sự chênh lệch này khiến tỷ lệ thành công (SR) giảm từ 31.03% xuống 11.33%.

**Giải pháp kiến trúc (TGIT - Trajectory-Grounded Instruction Translator):**
1.  **Frozen Navigator:** Giữ nguyên bộ điều hướng OpenFly (không retrain).
2.  **Data Augmentation:** Sử dụng LLM để tạo cặp dữ liệu (Original Command -> Weak Command).
3.  **Trajectory-Grounded Learning:** Module Translator không chỉ học từ văn bản mà còn học từ *kết quả* (outcome) của quỹ đạo. Nếu một lệnh Weak dẫn đến thất bại, hệ thống sẽ điều chỉnh trọng số hoặc thêm penalty vào loss function của Translator.
4.  **Zero-Shot Transfer:** Mô hình Translator được huấn luyện trên dữ liệu tổng hợp (Weak commands) nhưng phải có khả năng tổng quát hóa (generalize) sang các lệnh người dùng thực tế.

**Kiến trúc đề xuất:**
-   **Input:** Weak Instruction (text) + Current State (position, orientation, visual features).
-   **Module:** Transformer-based Encoder-Decoder (hoặc RNN/LSTM nếu tài nguyên hạn chế) để mã hóa ý định và giải mã thành chuỗi hành động (action sequence) hoặc lệnh chi tiết.
-   **Loss Function:** Kết hợp giữa Cross-Entropy Loss (cho việc dự đoán hành động/lệnh) và Trajectory Outcome Reward (RL-like signal).

### 2. SURGICAL CODE SOLUTION

Dưới đây là mã nguồn Python (PyTorch) cho module `TGITTranslator`. Code này giả định rằng bạn đã có `OpenFlyNavigator` (frozen) và một môi trường simulation (như AirVLN hoặc CityNav).

```python
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Tuple, Optional
import numpy as np

class TrajectoryGroundedInstructionTranslator(nn.Module):
    """
    TGIT: Translates weak, intent-driven instructions into 
    trajectory-aligned commands for a frozen navigator.
    
    Architecture:
    - Encoder: Processes weak instruction + current state.
    - Decoder: Generates a sequence of high-level actions or detailed command tokens.
    - Trajectory Grounding: Uses outcome rewards to modulate the loss.
    """
    
    def __init__(
        self,
        vocab_size: int,
        d_model: int = 256,
        nhead: int = 8,
        num_layers: int = 4,
        max_seq_len: int = 20,
        state_dim: int = 6  # x, y, z, yaw, pitch, roll
    ):
        super(TGITTranslator, self).__init__()
        
        self.vocab_size = vocab_size
        self.d_model = d_model
        self.max_seq_len = max_seq_len
        
        # 1. Instruction Encoder (Transformer Encoder)
        self.instruction_embedding = nn.Embedding(vocab_size, d_model)
        self.pos_encoding = nn.Parameter(torch.randn(1, max_seq_len, d_model))
        
        encoder_layer = nn.TransformerEncoderLayer(d_model, nhead, batch_first=True)
        self.instruction_encoder = nn.TransformerEncoder(encoder_layer, num_layers)
        
        # 2. State Encoder (MLP for current position/orientation)
        self.state_encoder = nn.Sequential(
            nn.Linear(state_dim, d_model),
            nn.ReLU(),
            nn.Linear(d_model, d_model)
        )
        
        # 3. Fusion Layer (Combine instruction and state)
        self.fusion_layer = nn.Sequential(
            nn.Linear(d_model * 2, d_model),
            nn.ReLU(),
            nn.LayerNorm(d_model)
        )
        
        # 4. Action Decoder (Generates detailed command tokens)
        self.action_decoder = nn.TransformerDecoder(
            nn.TransformerDecoderLayer(d_model, nhead, batch_first=True),
            num_layers
        )
        self.action_embedding = nn.Embedding(vocab_size, d_model)
        self.output_projection = nn.Linear(d_model, vocab_size)
        
        # 5. Trajectory Outcome Head (Predicts success probability based on state+instruction)
        self.outcome_head = nn.Sequential(
            nn.Linear(d_model, 128),
            nn.ReLU(),
            nn.Linear(128, 1)  # Sigmoid output for success probability
        )
        
        # Initialize weights
        self.apply(self._init_weights)
        
    def _init_weights(self, module):
        if isinstance(module, (nn.Linear, nn.Embedding)):
            nn.init.xavier_uniform_(module.weight.data)
            if module.bias is not None:
                nn.init.constant_(module.bias.data, 0.0)
        elif isinstance(module, nn.LayerNorm):
            nn.init.constant_(module.bias.data, 0.0)
            nn.init.constant_(module.weight.data, 1.0)

    def forward(
        self,
        weak_instructions: torch.Tensor,  # [Batch, SeqLen]
        states: torch.Tensor,             # [Batch, StateDim]
        target_commands: Optional[torch.Tensor] = None,  # [Batch, SeqLen] for training
        trajectory_rewards: Optional[torch.Tensor] = None  # [Batch] for grounding
    ) -> Dict[str, torch.Tensor]:
        """
        Forward pass.
        
        Args:
            weak_instructions: Tokenized weak instructions.
            states: Current agent state (pos, orientation).
            target_commands: Ground truth detailed commands (for training).
            trajectory_rewards: Reward from executing the command (for grounding).
            
        Returns:
            Dictionary with 'logits', 'outcome_prob', and 'loss' if training.
        """
        batch_size = weak_instructions.size(0)
        
        # 1. Encode Instruction
        instr_embeds = self.instruction_embedding(

⚡ <i>Qwen 3.8 27B (Groq LPU (Free) • 3.17s • $0.00)</i>