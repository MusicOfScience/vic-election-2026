"""Prospective rule approval and byte-level integrity, separate from model code."""
from __future__ import annotations
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

APPROVED_RULES_SHA256 = '747449970bf4a0bb4304e528c9e2ec37dd77420fffb1e1ee056fd0b4af4bdb01'
PROTOCOL = 'metadata/model-vnext-validation-protocol.json'
RULES = 'metadata/prospective-validation-approved-rules.json'
APPROVAL = 'metadata/prospective-validation-approval.json'
IMPLEMENTATION = 'metadata/prospective-validation-implementation.json'


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(value).hexdigest()


def read(root, path):
    return json.loads((Path(root) / path).read_text())


def material_rules(protocol):
    # Only these operational fields may differ from the approved PR #125 rules.
    result = json.loads(json.dumps(protocol))
    for key in ('status', 'approval', 'nextAction', 'scoringAuthorised', 'targetOutcomesLoaded'):
        result.pop(key, None)
    result['sealing'].pop('currentlySealedSnapshots', None)
    return result


def instant(value):
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        raise ValueError('timestamp must include timezone')
    return parsed.astimezone(timezone.utc)


def check_governance(root, *, implementation=True):
    protocol, approval, rules = (read(root, p) for p in (PROTOCOL, APPROVAL, RULES))
    if protocol['status'] not in ('approved-awaiting-registration-seal', 'approved-registration-sealed'):
        raise ValueError('approved protocol required')
    if approval['reviewerRole'] != 'project-owner' or approval['decision'] != 'approved':
        raise ValueError('explicit project-owner approval required')
    if protocol['approval'] != approval or approval['protocolId'] != protocol['protocolId']:
        raise ValueError('approval record mismatch')
    if instant(approval['recordedAt']) > datetime.now(timezone.utc):
        raise ValueError('approval cannot be in the future')
    if approval['approvedProtocolSha256'] != APPROVED_RULES_SHA256:
        raise ValueError('unregistered protocol fingerprint')
    if material_rules(protocol) != rules or digest(canonical(rules)) != approval['approvedProtocolSha256']:
        raise ValueError('approved material rules changed: new prospective version required')
    if protocol['scoringAuthorised'] or approval['scoringAuthorised'] or approval['productionAuthorised']:
        raise ValueError('this registration batch authorises neither scoring nor production')
    if protocol['status'] == 'approved-awaiting-registration-seal' and protocol['sealing']['currentlySealedSnapshots']:
        raise ValueError('unregistered protocol cannot contain seals')
    for path, expected in protocol['model']['engineSha256'].items():
        if digest((Path(root) / path).read_bytes()) != expected:
            raise ValueError(f'model changed: {path}')
    config = (Path(root) / protocol['model']['configurationPath']).read_text()
    structural = ''.join(line for line in config.splitlines(True) if not line.startswith('as_of:'))
    if digest(structural.encode()) != protocol['model']['structuralConfigurationSha256']:
        raise ValueError('structural configuration changed')
    if implementation:
        frozen = read(root, IMPLEMENTATION)
        if frozen['protocolSha256'] != approval['approvedProtocolSha256']:
            raise ValueError('implementation protocol mismatch')
        for path, expected in frozen['files'].items():
            if digest((Path(root) / path).read_bytes()) != expected:
                raise ValueError(f'unfrozen implementation change: {path}')
    if protocol['status'] == 'approved-registration-sealed':
        try:
            subprocess.run(['node', str(Path(root)/'scripts/validate-prospective-registration.mjs'), str(root)], check=True, capture_output=True)
        except subprocess.CalledProcessError as error:
            raise ValueError('existing sealed snapshot registry failed verification') from error
    return protocol, approval
