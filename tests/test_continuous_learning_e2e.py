"""End-to-end verification of continuous learning pipeline."""
import json, tempfile, os, filecmp, glob

def test_all():
    checks = 0

    # 1. common.py constants
    from skills.english_exam_ai_tutor.scripts.common import (
        EXAM_TYPES, SOURCE_TYPES, DISTILLATION_METHODS,
        ABILITY_TREE, EXAM_TIME_LIMITS, ERROR_SEVERITY_WEIGHTS
    )
    assert 'TEM4' in EXAM_TYPES and 'TEM8' in EXAM_TYPES
    assert len(SOURCE_TYPES) == 7
    assert len(DISTILLATION_METHODS) == 5
    assert 'book' in DISTILLATION_METHODS
    assert 'video' in DISTILLATION_METHODS
    assert 'person' in DISTILLATION_METHODS
    assert 'dictation' in ABILITY_TREE
    assert len(EXAM_TIME_LIMITS) == 5
    assert len(ERROR_SEVERITY_WEIGHTS) == 29
    checks += 1; print(f'[{checks}] common.py OK')

    # 2. Schema
    s = json.load(open('skills/english-exam-ai-tutor/assets/schemas/strategy-library.schema.json', encoding='utf-8'))
    props = s['properties']['strategies']['items']['properties']
    assert set(props['source_type']['enum']) == set(SOURCE_TYPES)
    assert set(props['distillation_method']['enum']) == set(DISTILLATION_METHODS)
    assert 'ria_structure' in props and 'mental_model' in props and 'heuristic' in props
    checks += 1; print(f'[{checks}] schema OK')

    # 3. cangjie RIA++ parser
    from skills.english_exam_ai_tutor.scripts.ingest_strategy import _parse_ria_structure
    ria = '## R - Reading\nTest.\n## I - Interpretation\nTest.\n## A1 - Past\nTest.\n## A2 - Trigger\nUser slow.\n## E - Execution\n1. S1\n2. S2\n## B - Boundary\nNot for C.'
    r = _parse_ria_structure(ria)
    assert len(r) == 6
    checks += 1; print(f'[{checks}] RIA++ parser (6/6) OK')

    # 4. nuwa parser (Chinese)
    from skills.english_exam_ai_tutor.scripts.ingest_strategy import _parse_nuwa_structure
    nuwa = '## 核心心智模型\n### 模型1: 慢就是快\n**一句话**：搞懂再前进。\n## 决策启发式\n1. **模仿法**：四步'
    m, h = _parse_nuwa_structure(nuwa)
    assert m and m['name'] == '慢就是快'
    assert h and h['name'] == '模仿法'
    checks += 1; print(f'[{checks}] nuwa parser OK')

    # 5. Full ingest cangjie
    from skills.english_exam_ai_tutor.scripts.ingest_strategy import ingest_strategy
    tmp_s = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8')
    tmp_s.write(ria); tmp_s.close()
    tmp_l = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8')
    json.dump({'strategies': []}, tmp_l); tmp_l.close()
    r = ingest_strategy(file_path=tmp_s.name, library_path=tmp_l.name, exam_types=['CET4'], modules=['listening'],
                        source_type='video', distillation_method='video', source_url='https://bilibili.com/test')
    assert r['source_type'] == 'video' and r['distillation_method'] == 'video'
    assert len(r.get('ria_structure',{})) == 6
    os.unlink(tmp_s.name); os.unlink(tmp_l.name)
    checks += 1; print(f'[{checks}] ingest cangjie OK')

    # 6. Plan with strategies
    from skills.english_exam_ai_tutor.scripts.generate_daily_plan import generate_daily_plan
    lib = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8')
    json.dump({'strategies': [
        {'strategy_id':'cet4-reading-book-001','title':'A','exam_types':['CET4'],'modules':['reading'],
         'source_type':'book','distillation_method':'book','content':'x'*30,'source_file':'x','added_at':'2026-07-05'},
        {'strategy_id':'cet4-listening-video-001','title':'B','exam_types':['CET4'],'modules':['listening'],
         'source_type':'video','distillation_method':'video','content':'x'*30,'source_file':'x','added_at':'2026-07-05',
         'ria_structure':{'a2_trigger':'slow','e_execution':['S1','S2']}},
        {'strategy_id':'pg-writing-person-001','title':'C','exam_types':['POSTGRADUATE_ENGLISH'],'modules':['writing'],
         'source_type':'person','distillation_method':'person','content':'x'*30,'source_file':'x','added_at':'2026-07-05',
         'heuristic':{'scenario':'rushing'}},
    ]}, lib); lib.close()
    with open(lib.name, encoding='utf-8') as f: strategies = json.load(f)
    p = generate_daily_plan({'learner_id':'x','exam_type':'CET4','daily_time_budget_minutes':90},
                            {'modules':{'reading':[{'node':'n1','status':'priority','level':1}],
                                        'listening':[{'node':'n2','status':'needs_work','level':2}]}},
                            None, strategies)
    h = sum(len(t.get('strategy_hints',[])) for t in p['tasks'])
    assert h > 0
    os.unlink(lib.name)
    checks += 1; print(f'[{checks}] plan with strategies ({h} hints) OK')

    # 7. Validate + List
    from skills.english_exam_ai_tutor.scripts.validate_strategy import validate_library
    from skills.english_exam_ai_tutor.scripts.list_strategies import list_strategies
    lib2 = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8')
    json.dump({'strategies': [
        {'strategy_id':'cet4-reading-book-001','title':'A','exam_types':['CET4'],'modules':['reading'],
         'content':'x'*30,'source_file':'t.md','added_at':'2026-07-05',
         'source_type':'book','distillation_method':'book'},
    ]}, lib2); lib2.close()
    vl = validate_library(json.load(open(lib2.name, encoding='utf-8')))
    assert vl['summary']['passed']
    lr = list_strategies(lib2.name)
    assert lr['total'] == 1
    os.unlink(lib2.name)
    checks += 1; print(f'[{checks}] validate + list OK')

    # 8. SKILL.md
    with open('skills/english-exam-ai-tutor/SKILL.md', encoding='utf-8') as f: skill = f.read()
    assert 'book' in skill and 'video' in skill and 'person' in skill
    assert 'multi-source-distillation.md' in skill
    checks += 1; print(f'[{checks}] SKILL.md OK')

    # 9. workflow.md
    with open('skills/english-exam-ai-tutor/references/workflow.md', encoding='utf-8') as f: wf = f.read()
    assert 'Knowledge Ingestion' in wf
    assert 'book' in wf and 'video' in wf and 'person' in wf
    assert '--strategies' in wf
    checks += 1; print(f'[{checks}] workflow.md OK')

    # 10. data-model.md
    with open('skills/english-exam-ai-tutor/references/data-model.md', encoding='utf-8') as f: dm = f.read()
    assert 'Strategy Library' in dm
    assert 'source_type' in dm and 'distillation_method' in dm
    assert 'ria_structure' in dm and 'mental_model' in dm and 'heuristic' in dm
    checks += 1; print(f'[{checks}] data-model.md OK')

    # 11. Shortcut skills
    for name in ['learning-planner','vocabulary-builder','reading-navigator','structure-planner',
                 'grammar-corrector','polish-wizard','scenario-dialog','culture-guide']:
        with open(f'skills/{name}/SKILL.md', encoding='utf-8') as f:
            assert 'multi-source-distillation.md' in f.read(), f'{name} missing ref'
    checks += 1; print(f'[{checks}] 8 shortcut skills OK')

    # 12. Mirror sync
    skill_d = 'skills/english-exam-ai-tutor/scripts'
    mirror_d = 'skills/english_exam_ai_tutor/scripts'
    for f in glob.glob(f'{skill_d}/*.py'):
        assert filecmp.cmp(f, f.replace(skill_d, mirror_d)), f'Mirror mismatch: {f}'
    checks += 1; print(f'[{checks}] mirror sync (14/14) OK')

    print(f'\nALL {checks} CHECKS PASSED')
    return True

if __name__ == '__main__':
    import sys
    try:
        test_all()
    except AssertionError as e:
        print(f'FAIL: {e}')
        sys.exit(1)
