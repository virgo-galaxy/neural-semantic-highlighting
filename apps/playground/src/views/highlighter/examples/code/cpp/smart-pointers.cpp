#include <memory>
#include <utility>

struct Node {
    int value;
    std::unique_ptr<Node> next;
};

std::unique_ptr<Node> prepend(std::unique_ptr<Node> head, int value) {
    auto node = std::make_unique<Node>();
    node->value = value;
    node->next = std::move(head);
    return node;
}
