"""AWK command backed by shared training infrastructure."""
from training.shared.spec import using
from training.shared.prepare import main
if __name__=="__main__":
    with using("awk"):main()
