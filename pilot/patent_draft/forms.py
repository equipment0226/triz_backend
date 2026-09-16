"""Deterministic editable review package. Official editor validation is separate."""
import hashlib
from html import escape
from io import BytesIO
import json
import zipfile
from .domain import canonical, digest, PatentError
from .drawings import svg, SAMPLE_IMAGE_NOTICE
from triz.display_terms import display_text, display_value

FORM_VERSION = 'KR_RULE21_2026-05-14_DRAFT_MAPPING_V1'
SOURCE_URL = 'https://www.law.go.kr/LSW/lsSideInfoP.do?docCls=jo&joBrNo=00&joNo=0021&lsiSeq=286191&urlMode=lsScJoRltInfoR'
SECTIONS = ('title', 'technical_field', 'background', 'problem', 'solution', 'effects', 'drawing_description', 'embodiments')
HEADINGS={'title':'발명의 명칭','technical_field':'기술분야','background':'발명의 배경이 되는 기술',
    'problem':'해결하려는 과제','solution':'과제의 해결 수단','effects':'발명의 효과',
    'drawing_description':'도면의 간단한 설명','embodiments':'발명을 실시하기 위한 구체적인 내용'}


def requirements(facts):
    required = [{'id': 'form14', 'name': '특허출원서', 'required': True},
                {'id': 'form15', 'name': '명세서·청구범위', 'required': True},
                {'id': 'form16', 'name': '요약서', 'required': True},
                {'id': 'form17', 'name': '필요 도면', 'required': facts.get('drawings_required'), 'condition': '발명의 이해에 필요한 도면'}]
    for key, label in [('agent', '대리권 증명서류'), ('priority', '우선권 증명서류'),
                       ('disclosure_exception', '공지예외 관련 증명서류'), ('sequence', '서열목록'),
                       ('deposit', '미생물 기탁 관련 증명서류'), ('assignment', '권리승계 관련 증명서류')]:
        required.append({'id': key, 'name': label, 'required': facts.get(key),
                         'status': 'NEEDS_FACTS' if facts.get(key) is None else 'REQUIRED' if facts[key] else 'NOT_APPLICABLE',
                         'condition': '해당 사실·절차 및 증명 필요성 검토'})
    return required


def archive(files):
    stream = BytesIO()
    with zipfile.ZipFile(stream, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        for name, data in sorted(files.items()):
            if '..' in name or name.startswith('/') or '\\' in name:
                raise ValueError('unsafe export name')
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o600 << 16
            z.writestr(info, data)
    return stream.getvalue()


def docx(paragraphs, image=None):
    text = ''.join('<w:p><w:pPr><w:spacing w:before="0" w:after="0" w:line="672" w:lineRule="auto"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:eastAsia="맑은 고딕"/><w:color w:val="000000"/><w:sz w:val="24"/></w:rPr><w:t xml:space="preserve">'+escape(p)+'</w:t></w:r></w:p>' for p in paragraphs)
    xml = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    if image:
        text += '<w:p><w:r><w:drawing><wp:inline xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"><wp:extent cx="4572000" cy="4572000"/><wp:docPr id="1" name="AI sample image" descr="'+escape(SAMPLE_IMAGE_NOTICE)+'"/><a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:nvPicPr><pic:cNvPr id="1" name="sample-1.png"/><pic:cNvPicPr/></pic:nvPicPr><pic:blipFill><a:blip xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" r:embed="rIdImage1"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill><pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="4572000" cy="4572000"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p><w:p><w:r><w:t>'+escape(SAMPLE_IMAGE_NOTICE)+'</w:t></w:r></w:p>'
    files = {
        '[Content_Types].xml': (xml+'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Default Extension="png" ContentType="image/png"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>').encode(),
        '_rels/.rels': (xml+'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>').encode(),
        'word/document.xml': (xml+'<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>'+text+'<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="2268" w:right="1134" w:bottom="1134" w:left="1417"/></w:sectPr></w:body></w:document>').encode()}
    if image:
        files['word/media/sample-1.png'] = image
        files['word/_rels/document.xml.rels'] = (xml+'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rIdImage1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/sample-1.png"/></Relationships>').encode()
    return archive(files)


def render(case, material, mode, reviews, checks, sample_image=None):
    from .form_registry import load
    registry,official_files=load()
    if case.get('form_registry_hash')!=digest(registry):
        raise PatentError('FORM_VERSION_CHANGED','공식 서식 버전이 변경됐습니다. 고정한 서식으로 다시 확인해야 합니다.')
    if mode not in ('ANNOTATED', 'REVIEWED'):
        raise PatentError('EXPORT_MODE', '내보내기 모드가 잘못됐습니다.', 422)
    if mode == 'REVIEWED' and case['document_status'] != 'DRAFT_READY':
        raise PatentError('REVIEW_REQUIRED', '필수 검토와 승인 완료 후 검토본을 내보낼 수 있습니다.')
    document = material.get('specification', {})
    invention = material.get('invention', {})
    claims = material.get('claims', {}).get('claims', [])
    drawing = material.get('drawings', {'drawings': []})
    facts = material.get('facts', {})
    title = display_text(document.get('title') or invention.get('title') or case['title'])
    form14 = ['【서류명】 특허출원서', '【발명의 명칭】 '+title,
              '【출원인】 '+(facts.get('applicant_name') or '[미입력]'),
              '【발명자】 '+(facts.get('inventor_names') or '[미입력]')]
    form15 = ['【명세서】','【발명의 설명】', '【발명의 명칭】',title]
    sections={s['id']:s for s in document.get('sections',[])}
    for section_id in SECTIONS[1:]:
        if section_id=='problem':form15.append('【발명의 내용】')
        section=sections.get(section_id,{})
        form15.extend(['【'+HEADINGS[section_id]+'】',section.get('text') or ('[미작성 또는 생략 사유] '+str(section.get('omission_reason') or '미확인'))])
    form15.append('【청구범위】')
    for claim in claims:
        form15 += ['【청구항 '+str(claim['number'])+'】', claim['text']]
    candidates=[d for d in drawing.get('drawings',[]) if d.get('kind')=='FILING_CANDIDATE']
    concepts=[d for d in drawing.get('drawings',[]) if d.get('kind')!='FILING_CANDIDATE']
    parts = {'14-application': form14, '15-specification-claims': form15,
             '16-abstract': ['【요약서】', '【요약】', document.get('abstract', '[미작성]')],
             '17-drawings': ['【도면】', SAMPLE_IMAGE_NOTICE]+([f'【도 {d["number"]}】 {d["caption"]}' for d in candidates] or ['[출원용 도면 후보 미확정]'])}
    if concepts:parts['concept-drawings']=['참고용 개념도',SAMPLE_IMAGE_NOTICE]+[f'도 {d["number"]} · {d["caption"]}' for d in concepts]
    files = dict(official_files)
    files['official-reference/registry.json']=canonical(registry).encode()
    for name, paragraphs in parts.items():
        paragraphs=[display_text(p) for p in paragraphs]
        files['editable/'+name+'.docx'] = docx(paragraphs)
        files['preview/'+name+'.html'] = ('<!doctype html><html lang="ko"><meta charset="utf-8"><title>'+escape(title)+
            '</title><body><p>특허 초안 — 공식 작성기 검증 미실행</p>'+''.join('<p>'+escape(p)+'</p>' for p in paragraphs)+'</body></html>').encode()
        files['text/'+name+'.md'] = '\n\n'.join(paragraphs).encode()
    for name, content in svg(drawing).items():
        filing=any(name==f'figure-{d["number"]}.svg' for d in candidates)
        files[('drawings/' if filing else 'concept-drawings/')+name] = content
    if sample_image:
        files['editable/sample-image.docx']=docx(['참고용 샘플 이미지',SAMPLE_IMAGE_NOTICE],sample_image)
        files['samples/sample-1.png'] = sample_image
        import base64
        preview = ('<!doctype html><html lang="ko"><meta charset="utf-8"><title>특허 샘플 이미지</title><figure><img alt="특허 샘플 이미지" src="data:image/png;base64,'+
            base64.b64encode(sample_image).decode()+'"><figcaption>'+escape(SAMPLE_IMAGE_NOTICE)+'</figcaption></figure></html>')
        files['preview/sample-image.html'] = preview.encode()
    files['internal/reviews.json'] = canonical(reviews).encode()
    files['internal/checks.json'] = canonical(checks).encode()
    files['internal/review-summary.md']=('\n\n'.join(display_text(r.get('summary','')) for r in reviews)+
        '\n\n'+'\n'.join(display_text(r['criterion'])+': '+display_text(r['outcome']) for r in checks)).encode()
    files['internal/attachment-checklist.json'] = canonical(requirements(facts)).encode()
    files['source/frozen-material.json'] = canonical(material).encode()
    manifest = {'case_id': case['case_id'], 'snapshot_id': case['snapshot_id'], 'epoch': case['epoch'],
        'mode': mode, 'document_status': case['document_status'], 'editor_validation': 'NOT_RUN',
        'official_form_source': SOURCE_URL, 'form_version': FORM_VERSION,
        'official_template_bytes_verified': True, 'official_source_registry_hash':digest(registry),
        'generated_files_officially_validated':False,'formats': ['DOCX', 'HTML', 'MARKDOWN', 'JSON', 'SVG'],
        'generated_sample_image_notice': SAMPLE_IMAGE_NOTICE, 'max_generated_images_per_case': 1,
        'excluded_actions': ['SIGNATURE', 'FILING', 'PAYMENT', 'ATTORNEY_CONTACT'],
        'files': {name: hashlib.sha256(value).hexdigest() for name, value in sorted(files.items())}}
    from .coverage import delivery_scope
    manifest['semantic_content_manifest_hash']=digest(delivery_scope(case,material))
    manifest['manifest_hash'] = digest(manifest)
    files['manifest.json'] = canonical(manifest).encode()
    return archive(files), manifest
