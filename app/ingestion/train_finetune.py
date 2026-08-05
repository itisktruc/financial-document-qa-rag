"""
train_finetune.py

Fine-tune vietocr trên dataset đã gán nhãn (label_tool.html xuất ra
train_annotation.txt / valid_annotation.txt trong dataset_finetune/).

CÁCH DÙNG (chạy trong CÙNG venv đang chạy parser.py - venv chính có torch/vietocr):

    python train_finetune.py \
        --data-root dataset_finetune \
        --base-model vgg_transformer \
        --iters 20000 \
        --export weights/vietocr_finetuned.pth

Sau khi train xong, set biến môi trường trước khi chạy parser.py:

    export VIETOCR_WEIGHTS=/duong/dan/toi/weights/vietocr_finetuned.pth

(khớp đúng biến VIETOCR_WEIGHTS đã có sẵn trong parser.py - KHÔNG cần sửa code).

GHI CHÚ QUAN TRỌNG:
- `pretrained=True` là bắt buộc cho fine-tune với vài nghìn mẫu - đây là
  TIẾP TỤC train từ weight gốc (transfer learning), KHÔNG phải train từ đầu.
  Train từ đầu (pretrained=False) với vài nghìn mẫu gần như chắc chắn cho kết
  quả tệ hơn hẳn so với model gốc.
- Nếu nhãn của bạn CÓ ký tự không nằm trong vocab mặc định của vietocr (hiếm,
  vd ký hiệu đặc biệt), cần cập nhật config['vocab'] TRƯỚC khi train, nếu
  không predictor sẽ lỗi hoặc bỏ qua ký tự đó. Script bên dưới có kiểm tra và
  CẢNH BÁO (không tự ý sửa vocab, vì mở rộng vocab cần cân nhắc kỹ - có thể
  ảnh hưởng tới lớp output cuối của model).
"""
import argparse
import os

from vietocr.tool.config import Cfg
from vietocr.model.trainer import Trainer


def _check_vocab_coverage(config, data_root, annotation_files):
    """Cảnh báo (không tự sửa) nếu nhãn chứa ký tự ngoài vocab hiện tại -
    train với ký tự lạ ngoài vocab thường khiến vietocr bỏ qua/lỗi ký tự đó."""
    vocab_chars = set(config["vocab"])
    label_chars = set()
    for ann in annotation_files:
        path = os.path.join(data_root, ann)
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as f:
            for line in f:
                parts = line.rstrip("\n").split("\t")
                if len(parts) >= 2:
                    label_chars.update(parts[1])
    missing = label_chars - vocab_chars
    if missing:
        print(
            f"[!] CẢNH BÁO: {len(missing)} ký tự trong nhãn KHÔNG có trong vocab "
            f"của model gốc ({config['vocab_name'] if 'vocab_name' in config else config.get('name','?')}): "
            f"{sorted(missing)!r}\n"
            f"    -> Các ký tự này nhiều khả năng sẽ KHÔNG được model học đúng. Nếu quan trọng, "
            f"cần cập nhật config['vocab'] TRƯỚC khi train (xem docstring script này)."
        )
    else:
        print("[OK] Toàn bộ ký tự trong nhãn đều nằm trong vocab hiện tại của model.")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data-root", default="dataset_finetune",
                     help="Thư mục chứa images/, train_annotation.txt, valid_annotation.txt")
    ap.add_argument("--train-annotation", default="train_annotation.txt")
    ap.add_argument("--valid-annotation", default="valid_annotation.txt")
    ap.add_argument("--base-model", default=os.getenv("VIETOCR_MODEL_NAME", "vgg_transformer"),
                     choices=["vgg_transformer", "vgg_seq2seq"],
                     help="Nên khớp với VIETOCR_MODEL_NAME đang dùng trong parser.py")
    ap.add_argument("--pretrained-weights", default=None,
                     help="Đường dẫn weight gốc để TIẾP TỤC fine-tune (để trống = dùng pretrained mặc định của vietocr)")
    ap.add_argument("--device", default=os.getenv("VIETOCR_DEVICE", "cuda:0"))
    ap.add_argument("--batch-size", type=int, default=16,
                     help="Giảm xuống 8 nếu gặp CUDA out of memory (GTX 1660 6GB nên bắt đầu từ 16)")
    ap.add_argument("--iters", type=int, default=20000)
    ap.add_argument("--print-every", type=int, default=200)
    ap.add_argument("--valid-every", type=int, default=1000)
    ap.add_argument("--export", default="weights/vietocr_finetuned.pth")
    ap.add_argument("--checkpoint", default="checkpoint/vietocr_finetune_checkpoint.pth")
    ap.add_argument("--resume-checkpoint", default=None,
                     help="Trỏ vào checkpoint cũ nếu bị ngắt giữa chừng, muốn train tiếp thay vì train lại từ đầu")
    args = ap.parse_args()

    os.makedirs(os.path.dirname(args.export) or ".", exist_ok=True)
    os.makedirs(os.path.dirname(args.checkpoint) or ".", exist_ok=True)

    config = Cfg.load_config_from_name(args.base_model)
    config["device"] = args.device
    if args.pretrained_weights:
        config["weights"] = args.pretrained_weights

    config["dataset"].update({
        "name": "financial_table_finetune",
        "data_root": args.data_root,
        "train_annotation": args.train_annotation,
        "valid_annotation": args.valid_annotation,
    })
    config["trainer"].update({
        "batch_size": args.batch_size,
        "print_every": args.print_every,
        "valid_every": args.valid_every,
        "iters": args.iters,
        "export": args.export,
        "checkpoint": args.checkpoint,
    })

    _check_vocab_coverage(
        config, args.data_root, [args.train_annotation, args.valid_annotation]
    )

    print(f"\n=== Bắt đầu fine-tune ===")
    print(f"  base model     : {args.base_model}")
    print(f"  device         : {args.device}")
    print(f"  data_root      : {args.data_root}")
    print(f"  batch_size     : {args.batch_size}  (giảm nếu CUDA out of memory)")
    print(f"  iters          : {args.iters}")
    print(f"  export weight  : {args.export}")
    print(f"  checkpoint     : {args.checkpoint}\n")

    # pretrained=True: BẮT BUỘC cho fine-tune - tải sẵn weight gốc làm điểm
    # xuất phát (transfer learning), không train từ đầu với vài nghìn mẫu.
    trainer = Trainer(config, pretrained=True)

    if args.resume_checkpoint:
        print(f"Nạp lại checkpoint để train tiếp: {args.resume_checkpoint}")
        trainer.load_checkpoint(args.resume_checkpoint)

    trainer.train()

    print(f"\n=== XONG ===")
    print(f"Weight đã fine-tune: {args.export}")
    print(f"Để dùng ngay trong parser.py, set biến môi trường:")
    print(f"    export VIETOCR_WEIGHTS={os.path.abspath(args.export)}")


if __name__ == "__main__":
    main()