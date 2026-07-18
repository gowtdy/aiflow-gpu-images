修改点：
  1、生成一个自动修改脚本， 将 build_assets/HyperFrames telemetry 的上报的域名调整为 https://mogofun.com, 方法调整为 /lapi/htmlvideo/batch/。
  修改telemetry的POSTHOG_HOST， 将 POSTHOG_HOST 调整为 https://mogofun.com
    package/cli/src/commands/telemetry/client, 调整 POSTHOG_HOST
    // const POSTHOG_HOST = "https://us.i.posthog.com";  // gowtd mod
    packages/studio/src/utils/studioTelemetry.ts:const POSTHOG_HOST
    packages/studio/src/telemetry/client.ts:const POSTHOG_HOST

  2、主要去掉 cli 和 init 中的自动更新逻辑。
    版本自动检查更新修改
    packages/cli/src/cli.ts
    packages/cli/src/commands/init.ts

  3、修改 templates
    CLAUDE.md
    AGENTS.md
    package/cli/src/templates/_shared/CLAUDE.md
    package/cli/src/templates/_shared/AGENTS.md


  4、调整 build_assets/scripts/build-frame.mjs 路径默认值
    - hyperframesDir：必须通过 --videodir <dir> 参数传入（不再默认 "."）
    - presetDir：默认改为 /app/hyperframes/skills/hyperframes-creative/frame-presets
    脚本：python3 modify/patch-build-frame.py

