import sys

if __name__ == "__main__":
    if "--check-runtime" in sys.argv:
        import torch
        import torchvision
        from sentence_transformers import SentenceTransformer
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from PySide6.QtWidgets import QApplication
        from gemma_desktop.core import Engine
        from gemma_desktop.chat import Chat
        assert torchvision.extension._has_ops()
        print("PACKAGED_RUNTIME_OK", flush=True)
        sys.exit(0)
    elif "--check-model" in sys.argv:
        from scripts.check_model import main
    else:
        from gemma_desktop.app import main
    main()
