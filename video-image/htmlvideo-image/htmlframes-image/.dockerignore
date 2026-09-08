# Builder-only context: shrink upload; CLI build-copy only needs warm-grain + a few skills.

bak/
example/
modify/
.git/
.DS_Store
**/.DS_Store
**/node_modules/
**/.bun/
**/.turbo/
**/coverage/
.env
.env.*
!.env.example
*.mp4
*.log

# Tests are not needed to compile the CLI (~47MB producer/tests alone).
build_assets/hyperframes/packages/*/tests/
build_assets/hyperframes/packages/producer/tests/

# Registry: build-copy only needs examples/warm-grain.
build_assets/hyperframes/registry/blocks/
build_assets/hyperframes/registry/components/

# Skills: build-copy only bundles hyperframes / hyperframes-cli / gsap (existsSync-guarded).
build_assets/hyperframes/skills/*
!build_assets/hyperframes/skills/hyperframes/
!build_assets/hyperframes/skills/hyperframes/**
!build_assets/hyperframes/skills/hyperframes-cli/
!build_assets/hyperframes/skills/hyperframes-cli/**
!build_assets/hyperframes/skills/gsap/
!build_assets/hyperframes/skills/gsap/**

# Prebuilt package outputs are regenerated inside the image.
build_assets/hyperframes/packages/*/dist/
