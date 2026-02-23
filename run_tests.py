import subprocess
import sys


def run_all():
    # Executa a suíte de testes
    rc = subprocess.call([sys.executable, "-m", "pytest", "tests/", "-q"]) 
    if rc != 0:
        print("pytest retornou falha. Interrompendo execução de demais passos.")
        return rc

    # Opcional: roda a simulação autônoma (modo --simulacao se suportado)
    try:
        subprocess.call([sys.executable, "main_autonomous.py", "--simulacao"])
    except Exception:
        print("Não foi possível executar main_autonomous.py --simulacao (pode não existir ou requerer setup).")

    # Roda o benchmark
    subprocess.call([sys.executable, "benchmark.py"]) 
    return 0


if __name__ == "__main__":
    sys.exit(run_all())
