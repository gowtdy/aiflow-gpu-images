修改点：
  1、上报地址修改
    package/cli/src/commands/telemetry/client, 调整 POSTHOG_HOST
    // const POSTHOG_HOST = "https://us.i.posthog.com";  // gowtd mod
    packages/studio/src/utils/studioTelemetry.ts:const POSTHOG_HOST
    packages/studio/src/telemetry/client.ts:const POSTHOG_HOST

  2、版本自动检查更新修改
    package/cli/src/cli.ts
    package/cli/src/commands/init.ts
    
