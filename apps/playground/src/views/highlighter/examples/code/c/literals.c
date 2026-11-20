// 保留原始内容 🌙
const char *message = "欢迎 🌌\n" "ready";
const unsigned long mask = 0xffUL;
const double scale = 0x1.fp+2;

int parse_digit(char value) {
    /* Names, strings and punctuation stay separate. */
    return value >= '0' && value <= '9' ? value - '0' : -1;
}
