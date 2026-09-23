import { installPayload } from './studymate.mjs';

export const inject = ['agentPresets'];

export async function apply(ctx) {
  const profile = ctx.get('profileContext');
  if (!profile || !ctx.agentPresets?.register) {
    throw new Error('StudyMate 原生插件需要 DSH 0.1.7-alpha.1+；旧版请使用 npx @yunmiao/studymate install。');
  }
  const { registration } = installPayload({
    native: true, profile: profile.name, dshHome: profile.home,
  });
  if (registration.patchChanged) {
    // The current Loader tree was composed before we removed the old declaration.
    // Do not register a second learning preset into that tree.
    throw new Error('StudyMate 已迁移旧安装器的学习模式配置，学习数据已保留。请重启 DSH 一次完成迁移。');
  }
  await ctx.effect(() => ctx.agentPresets.register(registration.config));
}
