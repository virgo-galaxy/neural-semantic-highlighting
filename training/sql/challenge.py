"""SQL command backed by shared training infrastructure."""
from training.shared.spec import using
from training.shared.challenge import main
if __name__=="__main__":
    with using("sql"):main()
