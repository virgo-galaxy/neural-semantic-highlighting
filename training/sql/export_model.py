"""SQL command backed by shared training infrastructure."""
from training.shared.spec import using
from training.shared.export_model import main
if __name__=="__main__":
    with using("sql"):main()
