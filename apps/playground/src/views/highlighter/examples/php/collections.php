<?php

function active_names(array $users): array {
    $active = array_filter($users, fn(array $user): bool => $user['active'] ?? false);
    return array_map(
        fn(array $user): string => strtoupper($user['name']),
        array_values($active),
    );
}
