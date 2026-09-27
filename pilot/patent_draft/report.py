"""One saved report model rendered consistently for web, Word and PDF."""
from io import BytesIO
from pathlib import Path
from html import escape
import math
import os
from .domain import digest, PatentError
from .forms import SECTIONS, HEADINGS

DOCX_MIME='application/vnd.openxmlformats-officedocument.wordprocessingml.document'


def font_path():
    candidates=[os.getenv('PATENT_REPORT_FONT',''),
        '/usr/share/fonts/truetype/nanum/NanumGothic.ttf',
        'C:/Windows/Fonts/malgun.ttf']
    path=next((Path(p) for p in candidates if p and Path(p).is_file()),None)
    if path is None:
        raise PatentError('REPORT_FONT_MISSING','한글 보고서 글꼴 설정이 필요합니다.',503)
    return str(path)


def model(case, material):
    document=material.get('specification')
    if not document or not material.get('claims'):
        raise PatentError('REPORT_NOT_READY','명세서와 청구범위가 작성된 후 보고서를 볼 수 있습니다.')
    sections={s['id']:s for s in document['sections']}
    body=[{'id':key,'heading':HEADINGS[key],
           'text':sections.get(key,{}).get('text') or sections.get(key,{}).get('omission_reason') or '미확인',
           'source_ids':sections.get(key,{}).get('source_ids',[])} for key in SECTIONS[1:]]
    body += [{'id':'claim-'+str(c['number']),'heading':'청구항 '+str(c['number']),
              'text':c['text'],'source_ids':c['feature_ids']} for c in material['claims']['claims']]
    body += [{'id':'abstract','heading':'요약서','text':document['abstract'],'source_ids':[]}]
    facts=material.get('facts',{})
    value={'report_version':'patent-report-v1','template_id':material.get('workflow_contract',{}).get('template_id'),
        'title':document['title'],'subtitle':'특허출원 검토용 초안',
        'applicant':facts.get('applicant_name') or '미확인',
        'inventors':facts.get('inventor_names') or '미확인',
        'sections':body,'drawings':material.get('drawings',{}).get('drawings',[]),
        'case_id':case['case_id'],'input_snapshot_id':case['snapshot_id'],
        'artifact_versions':{k:v for k,v in case['artifacts'].items() if k!='report'}}
    return {**value,'content_hash':digest(value)}


def diagram(drawing):
    """Render exactly the stored graph, including edge direction and labels."""
    from PIL import Image, ImageDraw, ImageFont
    nodes=drawing['nodes']
    cols=2; rows=max(1,math.ceil(len(nodes)/cols))
    image=Image.new('RGB',(1000,rows*200+80),'white')
    canvas=ImageDraw.Draw(image);font=ImageFont.truetype(font_path(),23)
    centers={n['id']:(250+(i%cols)*500,100+(i//cols)*200) for i,n in enumerate(nodes)}
    for edge in drawing['edges']:
        a,b=centers.get(edge['from']),centers.get(edge['to'])
        if not a or not b:continue
        dx,dy=b[0]-a[0],b[1]-a[1];length=max(1,math.hypot(dx,dy));ux,uy=dx/length,dy/length
        start=(a[0]+ux*90,a[1]+uy*55);end=(b[0]-ux*100,b[1]-uy*60)
        canvas.line([start,end],fill='black',width=3)
        canvas.polygon([end,(end[0]-ux*18-uy*8,end[1]-uy*18+ux*8),(end[0]-ux*18+uy*8,end[1]-uy*18-ux*8)],fill='black')
    for n in nodes:
        x,y=centers[n['id']]
        canvas.rounded_rectangle((x-185,y-45,x+185,y+45),radius=8,fill='white',outline='black',width=3)
        label=n['id']+' '+n['label']
        chunks=[];line=''
        for char in label:
            if canvas.textlength(line+char,font=font)>340:
                chunks.append(line);line=char
            else:line+=char
        chunks.append(line)
        # Size is bounded by the stored caption; no content is silently omitted.
        if len(chunks)>3:
            raise PatentError('DRAWING_LABEL_TOO_LONG','도면 명칭을 읽을 수 있도록 줄여 주세요.',422)
        for i,line in enumerate(chunks):canvas.text((x,y+(i-(len(chunks)-1)/2)*27),line,font=font,fill='black',anchor='mm')
    stream=BytesIO();image.save(stream,format='PNG');return stream.getvalue()


def render_word(value, figures):
    from docx import Document
    from docx.shared import Cm, Pt
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    document=Document();section=document.sections[0]
    section.page_width=Cm(21);section.page_height=Cm(29.7)
    section.top_margin=section.bottom_margin=Cm(2.1)
    section.left_margin=section.right_margin=Cm(2.2)
    for name in ('Normal','Title','Heading 1','Heading 2'):
        style=document.styles[name];style.font.name='Malgun Gothic'
        style.element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'),'맑은 고딕')
    document.styles['Normal'].font.size=Pt(10.5)
    document.styles['Normal'].paragraph_format.line_spacing=1.6
    document.add_paragraph(value['subtitle'],'Subtitle');document.add_heading(value['title'],0)
    document.add_paragraph('출원인: '+value['applicant']+'\n발명자: '+value['inventors'])
    for item in value['sections']:
        document.add_heading(item['heading'],1)
        for paragraph in item['text'].split('\n'):
            if paragraph.strip():document.add_paragraph(paragraph)
    for drawing,figure in zip(value['drawings'],figures):
        document.add_heading('도 '+str(drawing['number'])+' · '+drawing['caption'],1)
        document.add_paragraph('참고용 개념도' if drawing['kind']=='CONCEPT' else '검토용 도면 후보')
        from PIL import Image
        im=Image.open(BytesIO(figure));width=min(16.5,21*im.width/im.height)
        document.add_picture(BytesIO(figure),width=Cm(width))
        for edge in drawing['edges']:
            document.add_paragraph(edge['from']+' → '+edge['to']+': '+edge.get('label',''))
    footer=section.footer.paragraphs[0];footer.text='검토용 초안 · '+value['content_hash'][:12]+' · '
    field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');footer._p.append(field)
    stream=BytesIO();document.save(stream);return stream.getvalue()


def render_pdf(value, figures):
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
    font='PatentKorean'
    if font not in pdfmetrics.getRegisteredFontNames():pdfmetrics.registerFont(TTFont(font,font_path()))
    body=ParagraphStyle('body',fontName=font,fontSize=10.5,leading=18,spaceAfter=8,wordWrap='CJK')
    heading=ParagraphStyle('heading',parent=body,fontSize=14,leading=22,spaceBefore=16,spaceAfter=10,keepWithNext=True)
    title=ParagraphStyle('title',parent=heading,fontSize=22,leading=32)
    def paragraph(text,style=body):return Paragraph(escape(text).replace('\n','<br/>'),style)
    story=[paragraph(value['subtitle']),paragraph(value['title'],title),
           paragraph('출원인: '+value['applicant']+'\n발명자: '+value['inventors']),Spacer(1,10*mm)]
    for item in value['sections']:
        story.append(paragraph(item['heading'],heading))
        for part in item['text'].split('\n'):
            if part.strip():story.append(paragraph(part))
    for drawing,figure in zip(value['drawings'],figures):
        story.append(paragraph('도 '+str(drawing['number'])+' · '+drawing['caption'],heading))
        story.append(paragraph('참고용 개념도' if drawing['kind']=='CONCEPT' else '검토용 도면 후보'))
        image=Image(BytesIO(figure));scale=min(165*mm/image.imageWidth,190*mm/image.imageHeight)
        image.drawWidth=image.imageWidth*scale;image.drawHeight=image.imageHeight*scale;story.append(image)
        for edge in drawing['edges']:story.append(paragraph(edge['from']+' → '+edge['to']+': '+edge.get('label','')))
    def footer(canvas,doc):
        canvas.setFont(font,8);canvas.drawString(22*mm,12*mm,'검토용 초안 · '+value['content_hash'][:12])
        canvas.drawRightString(188*mm,12*mm,str(doc.page))
    stream=BytesIO()
    SimpleDocTemplate(stream,pagesize=A4,rightMargin=22*mm,leftMargin=22*mm,topMargin=21*mm,bottomMargin=21*mm,
                      title=value['title'],author='TRIZ Studio',invariant=1).build(story,onFirstPage=footer,onLaterPages=footer)
    return stream.getvalue()


def render(case, material):
    value=model(case,material)
    figures=[diagram(d) for d in value['drawings']]
    files={'docx':(DOCX_MIME,render_word(value,figures)), 'pdf':('application/pdf',render_pdf(value,figures))}
    files.update({'figure-'+str(i+1):('image/png',data) for i,data in enumerate(figures)})
    return value,files
