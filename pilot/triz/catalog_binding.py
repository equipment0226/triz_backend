"""Bind catalog identity and operating conditions before downstream handoffs."""
from copy import deepcopy


def conditions(*values):
    result=[]
    for value in values:
        for item in value if isinstance(value,list) else [value]:
            if item is not None and str(item).strip() and str(item).strip() not in result:
                result.append(str(item).strip())
    return result


def bind_standard(data, catalog):
    data=deepcopy(data) if isinstance(data,dict) else {}
    by_code={s['code']:s for s in catalog}
    for app in data.get('applications') or []:
        if not isinstance(app,dict): continue
        source=by_code.get(app.get('standard_code'))
        if not source: continue  # Checker must still see invalid model codes.
        app['standard_title']=source['title_ko']
        app['catalog_transformation']=source['transformation']
        app['catalog_conditions']=source['conditions']
        app['catalog_limitations']=source['limitations']
        app['catalog_sources']=source.get('sources',[])
        app['conditions']=conditions(source['conditions'],app.get('conditions'))
    return data


def bind_effect(data, catalog):
    data=deepcopy(data) if isinstance(data,dict) else {}
    by_id={e['id']:e for e in catalog}
    by_name={e['name']:e for e in catalog}
    for app in data.get('applications') or []:
        if not isinstance(app,dict): continue
        source=by_id.get(app.get('source_effect_id')) or by_name.get(app.get('effect_name'))
        app['source_effect_id']=source['id'] if source else None
        app['catalog_sources']=source.get('sources',[]) if source else []
        app['catalog_evidence_level']=source.get('evidence_level','기초 참고자료') if source else '카탈로그 외 추가 가설'
        if source:
            app.update(effect_name=source['name'],effect_domain=source.get('domain','PHYSICAL'),
                       principle=source['principle'],catalog_conditions=source.get('conditions',''),
                       catalog_function=source['function_ko'],catalog_mechanism_key=source.get('mechanism_key',''))
            app['conditions']=conditions(source.get('conditions'),app.get('conditions'))
    return data
