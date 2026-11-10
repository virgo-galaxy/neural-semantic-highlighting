<?php

namespace App\Model;

#[Entity(table: 'users')]
final readonly class User {
    public function __construct(
        public int $id,
        public string $name,
    ) {}

    public function label(): string {
        return "{$this->id}: {$this->name}";
    }
}
