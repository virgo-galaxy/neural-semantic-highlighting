#include <stdlib.h>

typedef struct Node {
    int value;
    struct Node *next;
} Node;

void destroy_list(Node *head) {
    while (head != NULL) {
        Node *next = head->next;
        free(head);
        head = next;
    }
}
