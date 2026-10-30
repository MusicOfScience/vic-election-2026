import { execFileSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
const root=fileURLToPath(new URL('..',import.meta.url));
export const researchAnchors=JSON.parse(readFileSync(new URL('../metadata/research-source-anchors.json',import.meta.url),'utf8'));
export function frozenResearchInput(ref,path){
 if(!/^[a-f0-9]{40}$/.test(ref) || path.startsWith('/') || path.split('/').includes('..')) throw new Error('Invalid frozen input identity');
 return execFileSync('git',['show',`${ref}:${path}`],{cwd:root,maxBuffer:100*1024*1024});
}
