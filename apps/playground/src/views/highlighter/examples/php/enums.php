<?php

enum Status: string {
    case Pending = 'pending';
    case Published = 'published';
}

function label(Status $status): string {
    return match ($status) {
        Status::Pending => 'Waiting',
        Status::Published => 'Ready',
    };
}
