import { execFileSync } from 'node:child_process';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { after } from 'node:test';
import { pathToFileURL } from 'node:url';
export async function frozenReadiness(){
 const dir=mkdtempSync(join(tmpdir(),'vic-frozen-readiness-'));
 execFileSync('git',['worktree','add','--detach',dir,'d254030d9f04066d04d6de280dc5d50700c60d66'],{stdio:'pipe'});
 after(()=>{execFileSync('git',['worktree','remove','--force',dir],{stdio:'pipe'});rmSync(dir,{recursive:true,force:true});});
 return import(pathToFileURL(join(dir,'scripts/check-release-readiness.mjs')).href);
}
