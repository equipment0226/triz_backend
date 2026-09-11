"""Build independently authored scientific reference entries; preserve literature separately.

The compact source below is editorial data, not LLM output. Each entry includes a
causal explanation, enabling conditions, limitations and a traceable reference.
No performance number is implied by a general mechanism.
"""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'triz/knowledge/curated_effects.json'
SOURCES={
 'heat':('OpenStax · Mechanisms of Heat Transfer','https://openstax.org/books/university-physics-volume-2/pages/1-6-mechanisms-of-heat-transfer'),
 'phase':('OpenStax · Phase Changes','https://openstax.org/books/university-physics-volume-2/pages/1-5-phase-changes'),
 'pump':('OpenStax · Refrigerators and Heat Pumps','https://openstax.org/books/university-physics-volume-2/pages/4-3-refrigerators-and-heat-pumps'),
 'nasa-thermal':('NASA · Small Spacecraft Thermal Control','https://www.nasa.gov/smallsat-institute/sst-soa/thermal-control/'),
 'thermoelectric':('NIST · Thermoelectric Measurements','https://www.nist.gov/programs-projects/thermoelectric-measurements'),
 'bernoulli':('OpenStax · Bernoulli’s Equation','https://openstax.org/books/university-physics-volume-1/pages/14-6-bernoullis-equation'),
 'viscosity':('OpenStax · Viscosity and Turbulence','https://openstax.org/books/university-physics-volume-1/pages/14-7-viscosity-and-turbulence'),
 'damping':('OpenStax · Damped Oscillations','https://openstax.org/books/university-physics-volume-1/pages/15-5-damped-oscillations'),
 'resonance':('OpenStax · Forced Oscillations','https://openstax.org/books/university-physics-volume-1/pages/15-6-forced-oscillations'),
 'magnetostriction':('COMSOL · Modeling Magnetostrictive Materials','https://doc.comsol.com/6.4/doc/com.comsol.help.sme/sme_ug_modeling.05.120.html'),
 'joule':('COMSOL · Joule Heating and Thermal Expansion','https://doc.comsol.com/6.3/doc/com.comsol.help.sme/sme_ug_multiphysics.18.06.html'),
 'electrohydro':('COMSOL · Electrohydrodynamics','https://doc.comsol.com/6.3/doc/com.comsol.help.mfl/mfl_ug_modeling.05.14.html'),
 'marangoni':('COMSOL · Modeling Marangoni Convection','https://www.comsol.com/blogs/modeling-marangoni-convection-with-comsol-multiphysics/'),
 'piezo':('PI · Displacement Behavior of Piezo Actuators','https://www.pi-usa.us/en/expertise/technology/piezo-technology/properties-piezo-actuators/displacement-behavior'),
 'lift':('NASA Glenn · Bernoulli and Newton','https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/bernoulli-and-newton/'),
 'boundary':('NASA Glenn · Boundary Layer','https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/boundary-layer/'),
 'airbearing':('New Way · How Air Bearings Work','https://www.newwayairbearings.com/news/blog/7287/how-do-bearings-work/'),
 'jamming':('Brown et al. · Universal robotic gripper based on granular jamming','https://pmc.ncbi.nlm.nih.gov/articles/PMC2973877/'),
 'acoustic-levitation':('Andrade et al. · Acoustic levitation in a single-axis acoustic levitator','https://arxiv.org/abs/1708.05988'),
 'tweezers':('Arthur Ashkin · Optical Tweezers Nobel Lecture','https://www.nobelprize.org/uploads/2018/10/ashkin-lecture.pdf'),
 'esp':('US EPA · Electrostatic Precipitators','https://www.epa.gov/air-emissions-monitoring-knowledge-base/monitoring-control-technique-electrostatic-precipitators'),
 'uf':('DuPont · Ultrafiltration','https://www.dupont.com/water/technologies/ultrafiltration-uf.html'),
 'ro':('DuPont · Reverse Osmosis','https://www.dupont.com/water/technologies/reverse-osmosis-ro.html'),
 'water':('DuPont · Water Treatment Technologies','https://www.dupont.com/water/technologies.html'),
 'electrolysis':('US DOE · Hydrogen Production: Electrolysis','https://www.energy.gov/cmei/fuels/hydrogen-production-electrolysis'),
 'quantum':('NIST · Atom-Based Quantum Sensing of Electromagnetic Fields','https://www.nist.gov/publications/atom-based-quantum-sensing-electromagnetic-fields'),
 'quantum-electric':('NIST · The Quantum Metrology Triangle','https://www.nist.gov/si-redefinition/ampere/ampere-quantum-metrology-triangle'),
 'lithography':('ASML · Lithography Principles','https://www.asml.com/en/technology/lithography-principles'),
}
SOURCES.update({
 'streaming':('COMSOL · Acoustic Streaming Theory','https://doc.comsol.com/6.3/doc/com.comsol.help.aco/aco_ug_streaming.13.12.html'),
 'hydrodynamic':('COMSOL · Hydrodynamic Bearing Theory','https://doc.comsol.com/6.4/doc/com.comsol.help.rotor/rotor_ug_hydrodynamicbearing.8.02.html'),
 'lyophilization':('FDA · Lyophilization of Parenterals','https://www.fda.gov/inspections-compliance-enforcement-and-criminal-investigations/inspection-guides/lyophilization-parenteral-793'),
 'sma':('NASA · Researchers Study Memory Materials','https://www.nas.nasa.gov/pubs/news/2010/news_03-03-10.html'),
 'nte':('NASA · Ultra-Stable Structures Using Negative Thermal Expansion','https://science.nasa.gov/science-research/science-enabling-technology/technology-highlights/a-new-alloy-is-enabling-ultra-stable-structures-needed-for-exoplanet-discovery/'),
 'faraday':('OpenStax · Faraday’s Law','https://openstax.org/books/university-physics-volume-2/pages/13-1-faradays-law'),
 'eddy':('OpenStax · Eddy Currents','https://openstax.org/books/university-physics-volume-2/pages/13-5-eddy-currents'),
 'hall':('OpenStax · The Hall Effect','https://openstax.org/books/university-physics-volume-2/pages/11-6-the-hall-effect'),
 'capacitor':('OpenStax · Capacitors and Capacitance','https://openstax.org/books/university-physics-volume-2/pages/8-1-capacitors-and-capacitance'),
 'semiconductor':('OpenStax · Semiconductor Devices','https://openstax.org/books/university-physics-volume-3/pages/9-7-semiconductor-devices'),
 'doping':('OpenStax · Semiconductors and Doping','https://openstax.org/books/university-physics-volume-3/pages/9-6-semiconductors-and-doping'),
 'photoelectric':('OpenStax · Photoelectric Effect','https://openstax.org/books/university-physics-volume-3/pages/6-2-photoelectric-effect'),
 'superconductor':('OpenStax · Superconductivity','https://openstax.org/books/university-physics-volume-3/pages/9-8-superconductivity'),
 'esc':('COMSOL · Electrostatic Chuck','https://doc.comsol.com/6.3/doc/com.comsol.help.models.mems.electrostatic_chuck/electrostatic_chuck.html'),
 'capacitive-sensor':('COMSOL · Capacitive Position Sensor','https://doc.comsol.com/6.4/doc/com.comsol.help.models.acdc.capacitive_position_sensor/capacitive_position_sensor.html'),
 'direct-piezo':('COMSOL · Piezoelectric Effect','https://www.comsol.com/multiphysics/piezoelectric-effect'),
 'piezoresistive':('COMSOL · Piezoresistive Effect','https://www.comsol.com/multiphysics/piezoresistive-effect?parent=electromechanical-effects-0182-172-152'),
 'battery':('US DOE · Batteries','https://www.energy.gov/science/doe-explainsbatteries'),
 'li-ion':('US DOE · Lithium-Ion Batteries for Stationary Energy Storage','https://www.energy.gov/oe/articles/fact-sheet-lithium-ion-batteries-stationary-energy-storage-october-2012'),
 'solar':('US DOE · How Does Solar Work?','https://www.energy.gov/cmei/systems/how-does-solar-work'),
})
SOURCES.update({
 'rheology':('COMSOL · Newtonian and Non-Newtonian Fluids','https://doc.comsol.com/6.4/doc/com.comsol.help.polymer/polymer_introduction.02.02.html'),
 'nonnewtonian':('COMSOL · Non-Newtonian Flow','https://doc.comsol.com/6.4/doc/com.comsol.help.mfl/mfl_ug_fluidflow_single.06.45.html'),
 'er':('Wen et al. · Giant electrorheological effect','https://www.nature.com/articles/nmat993'),
 'mr':('NASA · Fluid Physics on the ISS','https://www.nasa.gov/wp-content/uploads/2019/10/iss-fluid_physics_tagged.pdf?emrc=dd9a8d'),
 'viscoelastic':('COMSOL · Linear Viscoelasticity','https://doc.comsol.com/6.3/doc/com.comsol.help.sme/sme_ug_theory.06.029.html'),
 'solid-lubrication':('NASA · Solid Lubrication Fundamentals and Applications','https://ntrs.nasa.gov/citations/20010017158'),
 'mos2':('NASA · Friction and Wear of Solid Lubricating Films','https://ntrs.nasa.gov/api/citations/19990116894/downloads/19990116894.pdf'),
 'lotus':('Wang et al. · Design of robust superhydrophobic surfaces','https://www.nature.com/articles/s41586-020-2331-8'),
 'slips':('Wong et al. · Bioinspired self-repairing slippery surfaces','https://www.nature.com/articles/nature10447'),
 'gecko':('Nature Communications · Gecko spatulae and bio-mimics','https://www.nature.com/articles/ncomms9949'),
 'capillary':('COMSOL · Capillary Filling','https://doc.comsol.com/6.4/doc/com.comsol.help.models.mfl.capillary_filling_ls/capillary_filling_ls.html'),
 'wetting':('COMSOL · Contact Angle Boundary Conditions','https://doc.comsol.com/6.4/doc/com.comsol.help.mfl/mfl_ug_fluidflow_multi.07.33.html'),
 'maglev':('US DOE · How Maglev Works','https://www.energy.gov/articles/how-maglev-works'),
 'leidenfrost':('NASA · Film Boiling of Unconstrained Liquid Mass','https://ntrs.nasa.gov/api/citations/19700021089/downloads/19700021089.pdf?attachment=true'),
 'auxetic':('NASA · Auxetic Structures','https://ntrs.nasa.gov/api/citations/20150010164/downloads/20150010164.pdf?attachment=true'),
 'bistable':('Rafsanjani and Pasini · Bistable Auxetic Mechanical Metamaterials','https://arxiv.org/abs/1612.05988'),
 'diffusion-bond':('TWI · Diffusion Bonding','https://www.twi-global.com/what-we-do/our-processes/diffusion-bonding'),
 'fsw':('TWI · Friction Stir Welding','https://www.twi-global.com/what-we-do/research-and-technology/technologies/welding-joining-and-cutting/friction-welding/friction-stir-welding'),
 'ald':('NIST NanoFab · Atomic Layer Deposition','https://www.nist.gov/system/files/documents/cnst/nanofab/NanoFabNews_v2_i1_Feb10.pdf'),
})
FUNCTIONS={
 'HEAT':'열을 전달하거나 온도를 제어한다',
 'FLOW':'유체를 이동·분배한다',
 'HOLD':'물체를 지지·고정하거나 이동시킨다',
 'DAMP':'진동을 억제하거나 격리한다',
 'RHEO':'점도·강성을 제어한다',
 'SEPARATE':'혼합·분리를 촉진한다',
 'FILTER':'미세 입자를 포집·제거한다',
 'SHAPE':'형상·치수를 제어하거나 보상한다',
 'ENERGY':'에너지를 회수하거나 재활용한다',
 'SENSE':'상태를 측정·검출한다',
 'WAVE':'빛·전자기파·소리를 제어한다',
 'ELECTRIC':'전하·전류·전기적 특성을 제어한다',
 'SURFACE':'표면 특성을 제어한다',
 'FRICTION':'접촉 마찰을 줄인다',
 'REACTION':'물질을 변환·합성한다',
 'FORM':'물질을 접합·분리하거나 구조를 형성한다',
 'PROTECT':'손상을 방지·복구한다',
 'BIO':'생물학적 작용을 이용해 기능을 수행한다',
 'INFO':'정보를 전달·처리하거나 시스템을 제어한다',
}
groups={}
def add(function, rows, *,domain='PHYSICAL',industries='산업 공통'):
    for row in rows.strip().splitlines():
        if not row.strip() or row.startswith('#'):continue
        fields=[v.strip() for v in row.split('|')]
        if len(fields)!=11:raise ValueError((len(fields),row))
        key,name,en,principle,conditions,limitations,io,parameters,applications,refs,equation=fields
        inputs,outputs=io.split('>')
        sources=[{'identifier':'REF-'+r,'title':SOURCES[r][0],'url':SOURCES[r][1],
            'source_type':'REFERENCE','retrieval_scope':'reference_section','accessed_at':'2026-09-11',
            'supports':'기초 메커니즘과 조건을 확인하기 위한 참고 자료; 산업별 성능 보증 아님'} for r in refs.split(',')]
        e={'id':'SCI-'+key,'mechanism_key':key,'name':name,'name_en':en,'aliases':[name,en,key.replace('-',' ')],
            'domain':domain,'principle':principle,'conditions':conditions,'limitations':limitations,
            'inputs':inputs.split(';'),'outputs':outputs.split(';'),'parameters':parameters.split(';'),
            'applications':applications.split(';'),'industries':industries.split(';'),'sources':sources,
            'evidence_level':'기초 원리 · 조건을 명시한 편집 자료',
            'verification_scope':'과학 지식과 참고 문헌을 바탕으로 독립 작성; 제시 응용의 개별 실증·현장 성능을 보증하지 않음',
            'design_notes':'설계 검토 제안: 입력·출력의 기준선과 작동 조건을 계측하고, 이 항목의 한계가 나타나는 경계에서 성능을 비교한다.'}
        if equation!='-':
            e['equation'],e['equation_scope']=equation.split(' :: ')
        groups.setdefault(FUNCTIONS[function],[]).append(e)

add('HEAT','''
fourier-conduction|열전도|Fourier heat conduction|온도 구배가 있으면 격자 진동과 전자 등의 에너지 전달로 열이 고온에서 저온으로 이동한다. 열확산판은 단면과 전도 경로를 바꾸어 국소 열유속을 분산한다.|재료의 열전도율과 접촉 열저항을 알아야 하며 실제 방열을 위한 저온 경계가 필요하다.|계면·접착층 저항과 이방성 때문에 벌크 열전도율만으로 성능을 판단할 수 없다. 열확산판 자체가 열을 소멸시키지 않는다.|온도 차;고체 전도 경로>열유속;온도 분포 완화|열전도율 k;두께;단면적;접촉 열저항|반도체 열확산판;금형 온도 균일화;건물 단열|heat|q″=−k∇T :: 연속체·국소 열평형에서 등방성 재료의 푸리에 법칙; k의 온도 의존성은 별도 반영
forced-convection|강제 대류 열전달|Forced convection|팬이나 펌프가 유체를 이동시키면 가열된 유체가 교체되고 경계층을 통한 열 전달이 달라진다.|유체 순환 경로와 최종 방열부가 필요하며 유동 상태에 맞는 열전달 상관식을 사용한다.|유속 증가에는 압력 손실과 구동 전력이 따른다. 막힘·누설·오염이 성능을 제한한다.|유체 유동;벽면과 유체의 온도 차>열 수송|열전달계수 h;유속;점도;유로 직경|데이터센터 액랭;공정 열교환기;자동차 라디에이터|heat|Q̇=hA(Ts−T∞) :: 평균 열전달계수 h를 해당 형상·유동 조건에서 구한 경우
natural-convection|자연 대류|Natural convection|온도에 따른 밀도 차가 중력장에서 부력을 만들고 순환 유동으로 열을 운반한다.|유체 공간과 중력 방향을 고려해야 하며 열원과 냉각면 배치가 순환을 허용해야 한다.|미소중력에서는 통상적인 부력 대류가 약해진다. 강제 대류보다 제거 가능한 열유속이 제한될 수 있다.|온도 차;중력;유체>부력 유동;열 수송|열팽창계수;높이;온도 차;Rayleigh 수|수동 전자기기 냉각;건물 환기;저장 탱크 열관리|heat|-
thermal-radiation|열복사|Thermal radiation|물체는 온도와 파장별 방사율에 따라 전자기파를 방출하고 다른 물체의 복사를 흡수한다. 진공에서도 열교환이 가능하다.|표면의 분광 방사율, 시야계수와 주변 복사 온도를 파악해야 한다.|태양광 흡수와 주변 복사 유입을 무시하면 냉각량을 과대평가한다. 방사율은 파장·온도·표면 상태에 따라 달라진다.|표면 온도;복사 교환 경로>순 복사 열유속|방사율;면적;시야계수;절대온도|우주선 라디에이터;가열로;적외선 방열 코팅|heat,nasa-thermal|Q̇=εσA(T⁴−Tsur⁴) :: 큰 등온 주변에 노출된 회색 표면의 단순화 식; 온도는 K
capillary-heat-pipe|히트파이프의 증발·응축·모세관 순환|Capillary heat pipe|증발부의 액체가 잠열을 흡수하여 기화하고 증기가 응축부에서 열을 방출한다. 심지의 모세관 압력이 응축액을 증발부로 되돌린다.|작동유체·용기·심지의 재료 적합성, 적절한 충전량과 외부 냉각원이 필요하다.|모세관·비등·음속·비산 한계와 건조가 수송량을 제한한다. 자세·가속도·동결 조건에 따라 성능이 변한다.|열원;저온 응축부;작동유체>잠열 수송;온도 차 감소|심지 공극;충전율;증기압;배관 길이|노트북 냉각;우주 열제어;전력반도체 냉각|nasa-thermal|ΔPcap ≥ ΔPl+ΔPv+ΔPg :: 액체가 귀환하려면 모세관 구동 압력이 액체·증기·중력 압력 요구를 충족해야 함
phase-change-storage|상변화 잠열 저장|Phase-change thermal storage|융해 시 잠열을 흡수하고 응고 시 방출하는 물질로 열을 시간적으로 저장한다. 상변화 구간에서 온도 상승을 완충할 수 있다.|목표 온도에 맞는 상변화 온도와 충분한 재생 냉각 시간이 필요하다.|저장 용량은 유한하며 완전히 녹은 뒤에는 온도가 상승한다. 과냉각·상분리·부피 변화·낮은 열전도율을 검토한다.|일시적 열부하;상변화 물질>축열;온도 상승 지연|질량;잠열;융해 온도;열전도율|배터리 열 완충;콜드체인;건물 축열|phase,nasa-thermal|Q=mL :: 일정 압력에서 상변화 잠열만 계산; 현열과 용기 열용량은 별도
evaporative-cooling|증발 냉각|Evaporative cooling|액체가 기화할 때 필요한 잠열을 주변에서 흡수하여 표면이나 공기를 냉각한다.|증발할 액체와 증기 제거 경로가 필요하며 주변 습도와 압력이 구동력을 결정한다.|단순 공기 증발 냉각은 습도가 높으면 효과가 감소한다. 물 소비·농축·오염이 발생할 수 있다.|액체;증발 구동력>냉각;수증기|습도;기류;표면적;잠열|냉각탑;농산물 예냉;다공성 냉각면|phase|Q̇≈ṁevap L :: 증발 잠열 항만 고려한 에너지 수지
vapor-compression|증기 압축 냉동·히트펌프|Vapor-compression refrigeration|냉매를 압축·응축·팽창·증발시키는 순환으로 외부 일을 소비해 저온부의 열을 고온부로 옮긴다.|냉매의 상평형에 맞는 압력 범위와 두 열교환기, 압축기 및 팽창 장치가 필요하다.|냉각 용량에는 압축기 전력과 방열 용량이 함께 필요하다. 누설·서리·압축비가 성능을 제한한다.|전기 또는 축일;저온부 열>저온부 냉각;고온부 방열|증발·응축 온도;압축비;냉매 유량|공조;식품 냉동;공정 폐열 승온|pump|COPcool=Qc/W :: 정상 주기의 냉동 성능계수; W=Qh−Qc이며 열역학적 한계를 초과할 수 없음
peltier-cooling|펠티어 효과|Peltier effect|서로 다른 열전 재료를 통과하는 전류가 접합부에서 열을 흡수하거나 방출한다. 전류 방향을 바꾸면 가열·냉각 방향도 바뀐다.|냉각면 반대쪽에서 펌핑된 열과 줄열을 함께 방출할 방열부가 필요하다.|큰 온도 차에서는 냉각 용량과 효율이 감소한다. 전력만 공급하고 방열을 확보하지 않으면 양쪽이 가열될 수 있다.|직류 전류;열전 접합>열 펌핑;국소 온도 제어|전류;열전 계수;열저항;온도 차|레이저 온도 제어;소형 냉각;정밀 분석기|thermoelectric|Q̇P=ΠI :: 펠티어 항만 표현; 실제 순 냉각에는 줄열과 역방향 열전도를 포함
joule-heating|줄 가열|Joule heating|전도 전류가 저항성 매질을 통과하면서 전기 에너지가 열로 전환된다. 재료와 전극 구조로 발열 위치를 정할 수 있다.|전류 경로와 전기 저항, 방열 및 절연 조건을 정의해야 한다.|전류 집중과 온도에 따른 저항 변화가 국소 과열을 만든다. 전원 입력 이상의 열 에너지를 생성하는 효과가 아니다.|전류;전기 저항>열|전류밀도;저항률;전극 형상;열경계|저항로;박막 히터;식품 오믹 가열|joule|P=I²R :: 옴성 소자의 전기적 발열; 교류는 유효 저항과 실효값 사용
marangoni-convection|마랑고니 유동|Marangoni convection|온도 또는 조성 차에 따른 표면장력 구배가 계면 접선 방향 응력을 만들어 액체를 이동시킨다. 표면에서는 대체로 낮은 표면장력 쪽에서 높은 쪽으로 흐른다.|자유 표면이나 두 유체의 계면과 유지되는 표면장력 구배가 필요하다.|계면활성제·오염에 민감하며 구배가 큰 경우 불안정 유동이 생긴다. 재료마다 표면장력의 온도 의존성이 다르다.|온도 또는 조성 구배;액체 계면>표면 유동;열·물질 수송|dγ/dT;농도 구배;점도;계면 오염|용접 용융풀;잉크 건조;미세유체 혼합|marangoni|τt=∇sγ :: 계면의 접선 응력과 표면장력 구배의 관계
multilayer-insulation|다층 복사 단열|Multilayer insulation|저방사율 박막을 여러 층으로 두어 층 사이의 순 복사 교환을 줄인다. 간격재는 고체 접촉을 통한 열전도 증가를 억제한다.|층 사이 기체 전도가 충분히 낮은 진공과 적절한 층 간격이 필요하다.|대기압·층 압착·이음부 열교·수분 오염에서는 기대 단열 성능이 저하된다.|복사 열부하;저방사율 다층>열 침입 감소|층수;방사율;진공도;접촉 압력|우주선 단열;극저온 저장;진공 장비|nasa-thermal|-
variable-emittance|가변 방사율 열제어|Variable-emittance thermal control|표면의 적외선 방사율이나 라디에이터 노출 면적을 바꾸어 같은 온도에서 외부로 나가는 복사 열량을 조절한다.|주변 복사 환경과 표면의 실제 분광 응답을 알아야 하며 구동 방식별 전력·기구가 필요하다.|방사율 조절만으로 임의의 온도를 만들 수 없다. 자외선·원자산소·열주기에 따른 열화가 변수다.|표면 상태 제어;온도 차>방열량 조절|방사율 범위;응답 시간;시야계수|위성 루버;전기변색 열제어;가변 방열면|nasa-thermal|-
thermal-expansion-actuation|열팽창 구동|Thermal expansion actuation|재료의 온도 변화가 자유 열변형을 만들며, 구속이나 비대칭 형상은 이를 힘·변위로 바꾼다.|선팽창계수와 온도 분포, 기계 구속을 알아야 한다.|열관성 때문에 응답이 느려질 수 있고 구속 응력·열피로·주변 가열이 생긴다.|온도 변화;팽창 재료>변위;구속력|선팽창계수;길이;온도 차;구속 강성|MEMS 열 액추에이터;열 조립;간극 조정|joule|ΔL≈αL₀ΔT :: 작은 온도 구간의 자유 선형 팽창; 구속 응력과 α(T)는 별도
freeze-drying|동결 건조의 승화|Freeze drying by sublimation|동결된 용매를 액체 상태를 주로 거치지 않고 승화시켜 제거한다. 수증기는 차가운 응축부 등에 포집된다.|제품 온도·압력·열 공급을 용매 상평형과 제품의 붕괴 온도에 맞춰 제어한다.|건조가 느리고 에너지·진공 비용이 크다. 승화열을 과도하게 공급하면 용융·구조 붕괴가 생긴다.|동결 제품;감압;열>용매 제거;다공성 건조물|챔버 압력;선반 온도;제품 두께;응축기 온도|의약품 보존;식품 건조;다공성 재료 제조|phase|-
thermosiphon|중력식 열사이펀|Gravity thermosiphon|가열로 생긴 밀도 차 또는 증기·액체의 밀도 차가 순환을 유도한다. 2상 열사이펀에서는 응축액이 중력으로 증발부에 돌아온다.|응축액이 내려갈 수 있는 높이 배치와 막히지 않는 유로가 필요하다.|자세 제약과 유동 불안정, 건조·범람이 있다. 심지식 히트파이프와 달리 중력 귀환 조건을 무시할 수 없다.|열원;높이 차;냉각부>자연 순환;열 수송|고도 차;충전량;유로 직경;열부하|태양열 온수;전력기기 냉각;수동 열제어|nasa-thermal,heat|-
seebeck-generation|제벡 효과|Seebeck effect|서로 다른 전도체·반도체의 온도 구배에 따른 전하 운반 특성 차가 기전력을 만든다. 폐회로와 부하를 연결하면 일부 열유속을 전력으로 변환한다.|지속적인 고온부·저온부와 적합한 전기 부하가 필요하다.|열전달을 통한 손실과 접촉 저항이 성능을 제한한다. 온도 차가 사라지면 지속 발전하지 못한다.|온도 차;열전 재료>전압;전력|제벡 계수;열전도율;전기전도율;접촉 저항|폐열 회수;원격 센서 전원;열전대 측정|thermoelectric|V≈(SA−SB)ΔT :: 계수가 온도 구간에서 거의 일정한 두 재료의 개방 회로 기전력
heat-capacity-buffer|현열에 의한 열 완충|Sensible-heat buffering|물질의 온도를 변화시키는 데 필요한 열용량을 이용해 급격한 열부하를 시간에 걸쳐 흡수하거나 방출한다.|허용 온도 범위와 질량, 비열을 정의하고 나중에 열을 제거할 경로를 마련한다.|열용량은 무한한 방열 능력이 아니다. 저장물이 열평형에 도달하면 완충 여유가 사라진다.|변동 열부하;열용량>온도 변화 지연|질량;비열;열저항;허용 온도|공정 온도 안정화;축열조;측정기 열 안정화|phase|Q≈mcΔT :: 비열 변화와 상변화를 무시할 수 있는 구간
condensation-recovery|응축 잠열 회수|Condensation heat recovery|증기가 액체로 바뀌면서 방출하는 잠열을 냉각면 또는 다른 유체로 전달해 회수한다.|증기 분압에 대응하는 이슬점보다 낮은 표면과 응축수 배출이 필요하다.|비응축성 가스와 응축액 막이 열저항을 높인다. 부식성 성분이 응축될 수 있다.|증기;저온 열교환면>회수열;응축액|이슬점;비응축성 가스 농도;표면 상태|응축 보일러;증류 응축기;공정 폐열 회수|phase|Q̇≈ṁcond L :: 정상 응축의 잠열 항; 과열 증기 냉각과 과냉각은 별도
microchannel-cooling|미세유로 열교환|Microchannel heat exchange|유로의 크기를 줄이면 체적에 비해 큰 열교환 면적과 짧은 열전달 경로를 확보할 수 있다.|유로 분배 균일성, 압력 강하, 유체 청정도와 벽 재료를 함께 설계한다.|작은 유로는 막힘과 압력 손실에 민감하다. 비등을 이용하면 유동 불안정과 건조를 추가로 확인해야 한다.|냉각유체;미세 유로;열원>높은 면적 밀도의 열교환|수력직경;유량;압력강하;벽 두께|반도체 냉각;소형 열교환기;배터리 열관리|heat,viscosity|-
thermal-contact-engineering|계면 접촉 열저항 저감|Thermal contact resistance reduction|실제 고체 접촉은 거칠기 돌기의 제한된 면적에서 일어나므로 빈틈을 전도성 계면재로 채우거나 접촉 상태를 개선해 열저항을 줄인다.|계면재의 두께·압력·전기 절연 요구와 재료 적합성을 함께 고려한다.|재료의 높은 벌크 열전도율이 얇은 접합부 전체의 낮은 열저항을 보장하지 않는다. 펌프아웃·건조·노화가 생길 수 있다.|접촉 압력;계면 재료>계면 열저항 감소|표면 거칠기;접합 두께;압력;열주기|전자 패키지;배터리 냉각판;진공 장치 열접속|nasa-thermal|Rth=ΔT/Q̇ :: 해당 계면을 통과하는 정상 열류에서 정의한 열저항
spectral-thermal-coating|태양광 흡수율·적외선 방사율 분리|Spectrally selective thermal coating|입사 태양광과 열복사의 파장대가 다르다는 점을 이용해 코팅의 분광 흡수·방사 특성을 조절한다.|예상 태양 입사, 주변 복사와 코팅의 파장별 특성이 필요하다.|한 파장에서의 낮은 흡수율이 모든 파장에서 낮은 방사율을 뜻하지 않는다. 오염과 노화로 성능이 변한다.|입사 복사;선택적 광학 표면>흡열·방열 균형 조절|태양 흡수율;적외선 방사율;표면 온도|우주 열제어;태양열 집열기;복사 냉각 표면|nasa-thermal|-
thermal-strapping|유연 열 스트랩|Flexible thermal strap|전도성이 높은 얇은 금속박·편조선 등을 묶어 열전도 경로를 유지하면서 기계적 강성을 낮춘다.|양쪽 접합부의 접촉 열저항과 필요한 굽힘·진동 변위를 고려한다.|단면을 줄이면 유연해지지만 열저항이 커진다. 피로와 접합부 열화가 설계를 제한한다.|온도 차;유연 전도 경로>열 수송;기계적 분리|유효 단면;길이;굴곡;접촉 열저항|정밀 광학기기;위성 탑재체;극저온 장치|nasa-thermal|-
boiling-heat-transfer|핵비등 열전달|Nucleate boiling heat transfer|가열면의 핵생성 지점에서 기포가 성장·이탈하며 잠열 수송과 액체 교환을 촉진한다.|작동 압력과 포화 온도, 표면 젖음성, 안정적인 액체 공급을 관리한다.|임계 열유속을 넘으면 증기막이 형성되어 열전달이 급감하고 표면이 과열될 수 있다.|가열면;액체>증기 생성;열 제거|열유속;압력;표면 상태;과열도|증발기;공정 보일러;2상 전자 냉각|phase,nasa-thermal|-
thermal-isolation-gap|기체층·진공 간극 단열|Gas-gap and vacuum insulation|고체 열교를 줄이고 간극의 기체 전도·대류를 억제하여 열 침입을 감소시킨다. 진공은 기체 전달을 줄여도 복사를 없애지는 않는다.|압력 유지와 구조 지지, 복사 차폐를 함께 설계한다.|큰 간극은 대류를 허용할 수 있고 지지물은 열교가 된다. 진공 누설과 방출가스가 성능을 낮춘다.|온도 차;저전도 간극>열 누설 억제|간극;압력;표면 방사율;지지 단면|진공 단열재;극저온 용기;건축 복층 창|heat,nasa-thermal|-
''',industries='반도체·전자;에너지;건축;항공우주;식품;화학공정')

add('FLOW','''
pressure-driven-flow|압력차 구동 유동|Pressure-driven flow|압력 구배가 유체에 힘을 가해 점성 저항을 이기고 유동을 만든다. 유로 형상으로 유량 분배와 압력 손실을 조절한다.|유체 점도와 유로 단면, 유동 상태 및 펌프 운전점이 필요하다.|관 직경을 줄이면 층류에서 유동 저항이 크게 증가한다. 압축성·비뉴턴성·입구 효과에서는 단순식이 맞지 않는다.|압력차;유로>유량|점도;관 반경;길이;압력차|정밀 유량 제어;배관 설계;미세유체 저항|viscosity|Q=πr⁴ΔP/(8μL) :: 원형 직관의 정상·완전 발달·비압축성 뉴턴 유체 층류
venturi-entrainment|벤투리 압력 저하와 흡입|Venturi pressure reduction|유로 수축부에서 유속이 증가하면 적절한 조건에서 정압이 낮아져 측관 유체를 유입시킬 수 있다.|구동 유량과 압력, 혼합·확산 구간의 손실 및 흡입측 압력을 함께 고려한다.|좁은 통로가 스스로 에너지를 만드는 것은 아니다. 점성 손실·압축성·캐비테이션 때문에 이상식에서 벗어난다.|압력 에너지;수축 유로>국소 저압;흡입·혼합|면적비;유량;배압;압력 손실|이젝터;가스 혼합기;유량계|bernoulli|p+ρv²/2+ρgz=상수 :: 정상·비점성·비압축 유동의 같은 유선; 펌프 일과 손실이 없을 때
electroosmotic-flow|전기삼투 유동|Electroosmotic flow|대전된 벽 근처 전기이중층의 이온에 전기장이 힘을 가하고, 이온이 주변 액체를 끌어 유동을 만든다.|전해질과 대전 표면, 전극 및 전기장 경로가 필요하다.|기포 발생·줄 가열·표면 오염·이온강도 변화가 유동을 바꾼다. 모든 액체가 같은 방향으로 흐르지는 않는다.|접선 전기장;전기이중층>액체 이동|제타전위;전기장;점도;이온강도|미세유체 펌프;분석 칩;미세 혼합|electrohydro|uEO=−εζE/μ :: 얇은 이중층·작은 표면전도 등 Helmholtz–Smoluchowski 근사가 성립할 때
electrowetting|전기습윤|Electrowetting|액체·절연막·전극의 계면 에너지가 전압에 따라 변하면서 액적 접촉각과 젖는 면적이 변한다.|적합한 유전체·전극·액체 조합과 절연파괴를 피하는 전압 범위가 필요하다.|접촉각 포화·전하 포획·접촉선 고정 때문에 이상 관계가 전 범위에서 성립하지 않는다.|전압;액적;유전체 계면>접촉각 변화;액적 이동|정전용량;전압;표면장력;유전체 두께|디지털 미세유체;가변 초점 액체 렌즈;액적 분배|electrohydro|cosθ(V)=cosθ₀+C′V²/(2γ) :: 이상적인 절연막 전기습윤; 포화·누설·접촉각 이력은 제외
coanda-wall-jet|코안다 벽면 제트 부착|Coanda wall-jet attachment|제트가 주변 유체를 끌어들이고 인접 벽과의 압력 분포가 형성되면 제트가 곡면을 따라 편향될 수 있다.|노즐·벽 간격과 곡률, 제트 운동량 및 주변 경계 조건이 적합해야 한다.|모든 곡면에서 항상 부착되는 것은 아니며 압력 구배가 커지면 박리한다. 입자를 자동으로 분리하는 일반 법칙은 아니다.|유체 제트;인접 곡면>유동 방향 전환|곡률 반경;노즐 폭;유속;간격|에어 나이프;유체 증폭기;분사 방향 제어|boundary,lift|-
boundary-layer-control|경계층 제어|Boundary-layer control|벽 부근 저운동량 유체를 흡입하거나 운동량을 공급해 박리 위치와 표면 마찰을 바꾼다.|기준 유동의 Reynolds 수와 압력 구배를 파악하고 흡입·분사 에너지 수지를 포함한다.|박리 지연과 마찰 감소는 같은 결과가 아니다. 난류화를 통한 박리 지연은 표면 마찰을 늘릴 수 있다.|흡입 또는 분사;경계층>박리 지연;유동 안정화|분사 운동량;흡입량;압력 구배;표면 거칠기|항공기 날개;터보기계;덕트 확산기|boundary|-
hydrostatic-gas-bearing|기체 정압 베어링|Aerostatic bearing|외부에서 공급한 가압 기체가 제한기와 베어링 간극을 통과하면서 압력 분포를 형성해 하중을 지지한다.|청정 가압원과 적절한 간극·제한기·배기 경로가 필요하다.|공급 중단 시 접촉할 수 있다. 강성·하중·유량·진공 호환성의 상충을 검토한다.|가압 기체;미세 간극>비접촉 지지;낮은 마찰|공급 압력;간극;제한기;지지 면적|정밀 스테이지;반도체 검사;초정밀 스핀들|airbearing|F=∫A(p−pambient)dA :: 베어링 면의 실제 압력 분포를 적분한 지지력
hydrodynamic-lubrication|동압 윤활|Hydrodynamic lubrication|상대 운동하는 면 사이의 수렴 간극으로 점성 유체가 끌려 들어가 압력이 발생하고 두 고체를 분리한다.|충분한 윤활유 공급과 속도, 적절한 간극 형상이 필요하다.|저속·기동·정지에서는 완전 유체막이 사라질 수 있다. 발열·오염·점도 저하가 지지력을 바꾼다.|상대 운동;점성 윤활유;수렴 간극>유체막 지지;마찰 감소|속도;점도;간극;하중|저널 베어링;스러스트 베어링;터빈|viscosity|-
acoustic-streaming|음향 스트리밍|Acoustic streaming|진동 음장에서 점성 감쇠와 비선형 시간 평균 효과가 순방향 유동을 만든다. 입자에 직접 작용하는 음향 방사력과는 구분한다.|음파를 매질에 결합하고 벽·감쇠·주파수 조건을 제어해야 한다.|줄곧 비접촉·무발열인 기술은 아니다. 음향 흡수에 따른 발열과 캐비테이션을 확인한다.|음향 에너지;유체>평균 유동;혼합|주파수;음압;점도;유로 형상|미세유체 혼합;표면 세정;분석 칩|acoustic-levitation|-
''',industries='기계;반도체·전자;화학공정;물·환경;항공우주')

add('HOLD','''
optical-tweezers|광학 집게|Optical tweezers|집속광의 운동량 전달이 미세 입자에 힘을 가한다. 적절한 굴절률과 집속 조건에서 구배력이 입자를 초점 근처에 가두고 산란력이 이를 밀어낸다.|입자와 매질의 광학 성질, 충분한 개구수와 안정적인 집속이 필요하다.|광흡수에 따른 가열·광손상과 작은 포획력이 제한이다. 불투명한 거대 물체의 일반 지지 수단이 아니다.|집속 레이저;미세 입자>비접촉 포획;미세 힘 인가|광출력;개구수;입자 크기;굴절률 차|세포 연구;미세 조립;단분자 힘 측정|tweezers|-
acoustic-levitation|음향 방사력 부상|Acoustic levitation|음장의 공간 구배와 입자·매질의 밀도 및 압축성 차에 의해 시간 평균 음향 방사력이 생긴다. 중력을 상쇄하는 안정 위치에서 입자나 액적을 지지한다.|음장 형상과 입자의 음향 대비, 크기·질량에 맞는 주파수와 음압이 필요하다.|음향 대비에 따라 안정 위치가 달라지므로 모든 대상이 압력 마디에 모인다고 단정할 수 없다. 발열·변형·포획 안정성이 제한이다.|음장;입자 또는 액적>비접촉 부상;위치 제어|음압;주파수;입자 크기;음향 대비|비접촉 반응;액적 조작;민감 시료 처리|acoustic-levitation|-
granular-jamming|입자 재밍 그리퍼|Granular jamming gripper|유연 막 안의 입자층이 대상 형상에 순응한 뒤 감압으로 압착되면 입자 간 마찰과 얽힘이 증가해 형상을 고정한다.|기밀 막과 입자 충전, 충분한 접촉·형상 감싸기 및 압력 차가 필요하다.|흡착·마찰·형상 잠금의 기여가 대상마다 다르다. 날카로운 모서리, 막 파손과 작은 접촉 면적이 성능을 제한한다.|압력 차;유연 막;입자층>강성 증가;적응형 파지|입도;충전율;진공도;막 강성|물류 로봇;다품종 부품 취급;취약 물체 파지|jamming|-
''',industries='로봇·자동화;의료·바이오 연구;반도체·전자;정밀기계')

add('SHAPE','''
converse-piezoelectricity|역압전 효과|Converse piezoelectric effect|압전 재료에 전기장을 가하면 결정의 전기·기계 결합에 의해 변형이 발생한다. 적층 구조로 변위를 합산하거나 기구로 확대할 수 있다.|분극 방향과 전계·예압·온도 범위가 적합해야 한다.|히스테리시스·크리프·인장 취약성·제한된 행정이 있다. 높은 정확도에는 위치 피드백이 유용하다.|전기장;압전 재료>미세 변위;구동력|압전 계수;전압;층수;예압|정밀 스테이지;초음파 트랜스듀서;잉크젯|piezo|S≈dE :: 작은 신호의 단순 단축 근사; 일반적으로 탄성 응력 항과 이방성 텐서 포함
magnetostriction|자왜 효과|Magnetostriction|자성 재료의 자화 상태가 변하면서 자기·탄성 결합에 의해 치수가 바뀐다. 자구 재배열과 재료 이방성이 변형 방향과 크기에 영향을 준다.|적절한 자성 재료, 자계 방향과 바이어스·예압을 설정한다.|자기 포화·히스테리시스·와전류 발열이 있다. 자왜의 Joule 효과는 전기 저항의 줄 가열과 다른 현상이다.|자기장;자왜 재료>변형;진동|자계;예압;바이어스;온도|소나;정밀 액추에이터;진동 구동|magnetostriction|-
villari-effect|역자왜·빌라리 효과|Inverse magnetostriction / Villari effect|자성 재료에 응력을 가하면 자기 탄성 에너지가 바뀌어 자화와 투자율이 변한다. 이 변화를 전기·자기 센서로 읽을 수 있다.|응력과 자계 방향, 재료의 자기 이력 및 바이어스를 관리한다.|온도·잔류 응력·자기 히스테리시스가 측정에 함께 반영된다. 재료별 교정이 필요하다.|기계 응력;자성 재료>자기 상태 변화|응력;자계;투자율;온도|토크 센서;하중 감지;구조 상태 감시|magnetostriction|-
''',industries='정밀기계;반도체·전자;센서;의료기기;해양')

add('DAMP','''
viscous-damping|점성 감쇠|Viscous damping|속도에 반대되는 저항력이 기계적 운동 에너지를 열로 소산시켜 진동 진폭을 낮춘다.|운동 주파수·온도 범위에서 유효한 감쇠 계수와 열 방출 경로가 필요하다.|큰 감쇠가 모든 조건의 진동 전달을 줄이지는 않는다. 점도·씰 마찰·비선형성이 단순 모델에서 벗어날 수 있다.|상대 속도;점성 저항>진동 에너지 소산|감쇠 계수;속도;온도;스트로크|자동차 댐퍼;기계 방진;계측기 안정화|damping|F=−cv :: 선형 점성 감쇠 근사
resonant-absorber|동조 질량 감쇠기|Tuned mass damper|주 구조에 연결된 보조 질량·스프링이 목표 주파수 부근에서 상대 운동하여 주 구조 응답을 줄이고 감쇠부에서 에너지를 소산한다.|목표 모드의 주파수와 모달 질량, 설치 위치에 맞춘 동조가 필요하다.|협대역 성능이며 주파수 변화와 질량·공간 제약에 민감하다. 보조 질량의 큰 변위를 수용해야 한다.|구조 진동;보조 질량·스프링>목표 모드 응답 감소|질량비;동조 주파수;감쇠비;행정|고층건물;공작기계;회전기계|resonance,damping|fn=(1/2π)√(k/m) :: 단자유도 보조 진동자의 고유진동수; 최적 동조는 결합 시스템 기준
vibration-isolation|탄성 지지 진동 절연|Elastic vibration isolation|탄성 지지로 지지체와 장비 사이에 상대 운동을 허용하여 높은 주파수의 운동 전달을 낮춘다.|장비 질량·지지 강성·감쇠와 입력 주파수 범위를 함께 정한다.|고유진동수 부근에서는 공진으로 응답이 증폭될 수 있다. 정적 처짐과 자세 안정성도 확보해야 한다.|기초 진동;탄성 지지>고주파 진동 전달 감소|고유진동수;감쇠비;질량;강성|정밀 계측대;건물 면진;장비 마운트|resonance,damping|r=f/fn :: 선형 단자유도 기초 가진에서 변위 전달률이 1보다 작아지는 기본 경계는 r>√2
''',industries='건설;기계;자동차·철도;정밀 계측')

add('FILTER','''
electrostatic-precipitation|전기집진|Electrostatic precipitation|기체 중 입자를 대전시키고 전기장으로 집진 전극 쪽에 이동시켜 유동에서 제거한다.|입자 대전·전기장·체류 시간과 포집 후 분진 제거가 필요하다.|입자 전기저항·가스 조성·역코로나·재비산이 효율을 바꾼다. 고전압과 방전 부산물을 관리한다.|입자 포함 기체;고전압>입자 포집|전계;대전량;입자 저항률;유속|발전 배기가스;제철 집진;공정 분진 제어|esp|F=qE :: 대전 입자의 전기력 항; 실제 이동에는 항력과 난류 등을 포함
ultrafiltration|한외여과|Ultrafiltration|막의 기공과 용질·입자의 크기 및 상호작용 차이를 이용해 콜로이드·고분자 등을 압력차로 분리한다.|목표 성분에 맞는 막과 막간 압력, 유속·세정 조건을 정한다.|용존 소형 이온 제거를 일반적으로 보장하지 않는다. 오염·농도분극·막 손상에 따라 분리 성능이 변한다.|압력차;현탁액;다공성 막>투과액;농축액|막간 압력;분획분자량;표면 전하;유속|식품 단백질 농축;상수 전처리;바이오 공정|uf|-
''',industries='발전;금속;식품;제약;물·환경')

add('SEPARATE','''
reverse-osmosis|역삼투|Reverse osmosis|반투과성 막 양측의 삼투압 차보다 큰 유효 수압 차를 가해 용매가 통상적인 삼투 방향과 반대로 이동하도록 한다.|막의 선택성·내압성과 공급수 전처리, 농축수 배출 경로가 필요하다.|단순히 압력을 가하는 것만으로 충분하지 않다. 농도분극·스케일·막 산화·회수율 증가가 구동력과 수명을 제한한다.|삼투압 차를 넘는 수압;용액;막>용매 투과;용질 농축|ΔP;Δπ;막 투과도;염 농도;회수율|해수 담수화;초순수;공정수 재이용|ro|Jw=A(ΔP−Δπ) :: 용액-확산형 막의 단순 물 플럭스 관계; 유효 막 표면 농도와 압력 기준
nanofiltration|나노여과|Nanofiltration|작은 유효 기공과 막 표면 전하가 크기 배제·전기적 배제에 함께 기여해 용질별 투과 차이를 만든다.|막과 용액의 pH·이온강도·분자 특성 및 압력 조건이 맞아야 한다.|다가 이온과 유기물에 대한 선택성이 막마다 다르다. 모든 단가 이온을 완전히 제거하는 역삼투와 동일한 성능은 아니다.|압력차;용액;선택막>부분 탈염;선택적 농축|막 전하;기공 특성;pH;이온강도|연수화;색도 제거;공정 용질 회수|water|-
electrophoresis|전기영동|Electrophoresis|전하를 띤 입자·분자에 전기장이 힘을 가해 매질에 대해 이동시키며, 전기영동 이동도 차이로 분리할 수 있다.|대상의 전하 상태와 완충액, 전기장 및 열 관리가 필요하다.|전기삼투 배경 유동과 확산·줄 가열이 분리도를 바꾼다. 전하가 없는 분자의 직접 이동에는 별도 원리가 필요하다.|전기장;대전 입자 또는 분자>상대 이동;분리|이동도;pH;전기장;이온강도|단백질·DNA 분석;콜로이드 조작;입자 특성 분석|electrohydro|v=μeE :: 해당 매질·조건의 전기영동 이동도 μe를 사용한 선형 영역
dielectrophoresis|유전영동|Dielectrophoresis|불균일 전기장에서 분극된 입자의 양쪽에 다른 힘이 작용해 순힘이 생긴다. 입자와 매질의 복소 유전율 차이가 이동 방향을 결정한다.|전기장 구배와 적절한 주파수, 입자·매질의 유전율 및 전도도가 필요하다.|입자가 반드시 고전계 영역으로 이동하는 것은 아니다. 줄 가열과 전극 반응, 다른 전기유체 유동이 영향을 준다.|불균일 전기장;분극 가능한 입자>선택적 이동;포획|주파수;전계 구배;복소 유전율;입자 크기|세포 분류;입자 조립;미세유체 농축|electrohydro|FDEP∝r³ Re[K(ω)]∇(Erms²) :: 구형 입자·쌍극자 근사; K는 매질 대비 복소 분극 인자
magnetophoresis|자기영동|Magnetophoresis|공간적으로 불균일한 자기장이 입자와 주변 매질의 자화 특성 차이에 따라 순힘을 만든다.|자기장 구배와 충분한 자화 대비가 필요하며 비자성 표적에는 자성 표지 등을 사용할 수 있다.|균일한 자기장만으로 일반적인 병진 분리를 얻는다고 가정하면 안 된다. 유체 항력·응집·잔류 자화가 영향을 준다.|자기장 구배;자화 대비>입자 이동;자기 분리|자기 감수율 차;자계 구배;입도;유량|광물 선별;자성 비드 분리;금속 오염 제거|electrohydro|-
''',industries='물·환경;화학공정;식품;의료·바이오;광업·금속')

add('SENSE','''
hall-effect|홀 효과|Hall effect|전류를 운반하는 전하가 횡방향 자기력으로 편향되어 전하 축적과 횡전압을 만든다. 전압을 읽어 자기장이나 전류를 추정한다.|소자의 전류 방향과 자기장 방향, 운반자 특성 및 온도를 알아야 한다.|오프셋과 온도 드리프트, 다중 운반자 전도가 단순 모델을 벗어나게 한다. 외부 자계와 측정 대상 전류의 기여를 구분한다.|바이어스 전류;수직 자기장>홀 전압|운반자 밀도;전류;두께;온도|비접촉 전류계;위치·회전 센서;반도체 물성 측정|hall|VH=IB/(nqt) :: 단일 운반자·균일 두께의 단순 홀 바 형상에서 부호 규약에 따라 사용
capacitive-sensing|정전용량 감지|Capacitive sensing|전극 간 거리·겹침 면적 또는 주변 유전율 변화가 정전용량을 바꾼다. 변화량을 읽어 위치·액면·압력 등을 추정한다.|전극 형상과 접지·차폐, 기생 정전용량을 고려한 측정 회로가 필요하다.|습도·오염·주변 물체에 민감하다. 곡면이나 가장자리 전계가 강하면 평행판 근사가 부정확하다.|형상 또는 유전율 변화>정전용량 변화|전극 간격;면적;유전율;기생 용량|터치 센서;액면계;MEMS 압력계|capacitive-sensor|C≈εA/d :: 가장자리 효과가 작은 평행판·균일 유전체 근사
direct-piezoelectricity|정압전 효과|Direct piezoelectric effect|압전 재료의 응력이 전기 분극을 변화시켜 전극에 전하를 발생시킨다. 힘·진동·음압을 전기 신호로 바꿀 수 있다.|결정 방향·분극 상태와 전극, 적절한 고입력저항 또는 전하 증폭기가 필요하다.|누설 전류 때문에 장시간 정적 하중 측정에는 한계가 있다. 온도에 따른 초전 신호와 기계적 공진을 구분한다.|기계 응력>전하;전압|압전 계수;강성;정전용량;누설|가속도계;초음파 수신;압력 펄스 감지|direct-piezo|D=dT+εE :: 선형 압전 구성식의 전기 변위 D; T는 응력이며 일반적으로 텐서식
piezoresistive-sensing|압저항 효과|Piezoresistive effect|응력에 의해 재료의 전하 운반 특성과 비저항이 변한다. 반도체에서는 단순 치수 변화 외에 밴드 구조 변화가 크게 기여할 수 있다.|결정 방향·도핑·온도와 응력 분포에 맞는 압저항 계수가 필요하다.|압전처럼 스스로 전하를 생성하는 원리가 아니다. 바이어스 전원과 온도 보상, 자기 발열 관리가 필요하다.|응력;전기 바이어스>저항 변화|압저항 계수;결정 방향;온도;도핑|MEMS 압력계;하중 센서;미세 캔틸레버|piezoresistive|Δρ/ρ≈πσ :: 작은 응력에서 단축 단순화; 일반식은 이방성 압저항 텐서
eddy-current-sensing|와전류 비접촉 감지|Eddy-current sensing|교류 자기장이 도전성 대상에 와전류를 만들고 그 반작용이 코일의 임피던스를 바꾼다. 이를 간극·결함·재료 특성 변화로 해석한다.|도전성 대상과 교류 코일, 주파수별 교정이 필요하다.|리프트오프와 전도도·투자율·온도 변화가 결함 신호와 섞인다. 비도전성 대상에는 그대로 적용할 수 없다.|교류 자계;도전성 대상>코일 임피던스 변화|주파수;간극;전도도;투자율|금속 균열 검사;축 변위계;도금 두께 측정|eddy|δ≈√(2/(ωμσ)) :: 좋은 도체의 평면파·선형 매질 근사 표피 깊이; 형상 효과는 별도
photoelectric-emission|외부 광전 효과|Photoelectric emission|충분한 에너지의 광자가 물질의 전자를 표면 밖으로 방출시킨다. 입사 광자 수와 광전자 수의 관계를 계측에 이용한다.|광자 에너지가 표면 일함수 조건을 충족하고 방출 전자를 수집할 환경이 필요하다.|표면 오염과 일함수, 수집 효율이 중요하다. 광자 에너지가 문턱 아래이면 단일 광자 과정에서 세기 증가만으로 방출하지 않는다.|빛;광전면>방출 전자|파장;일함수;양자효율;바이어스|광전자 분광;광전관;전자원|photoelectric|Kmax=hf−Φ :: 단일 광자 광전자 방출에서 최대 운동 에너지; 공간전하·다광자 과정은 제외
photodiode|반도체 광다이오드|Semiconductor photodiode|흡수된 광자가 전자·정공 쌍을 만들고 접합의 전기장 및 확산이 이를 분리·수집하여 광전류를 만든다.|흡수 가능한 파장과 접합 구조, 읽기 회로 및 필요시 역바이어스가 필요하다.|암전류·포화·잡음·접합 용량이 감도와 속도를 제한한다. 모든 입사 광자가 유효 전류로 변환되지는 않는다.|광자>광전류|파장;양자효율;접합 용량;암전류|광통신 수신;광학 계측;이미지 센서|semiconductor|Iph≈ηqP/(hf) :: 단색광·선형 응답·내부 증배가 없는 광검출기의 수집 전류
atomic-magnetometry|원자 스핀 자기계|Atomic spin magnetometry|원자 스핀의 편극·세차와 자기장에 따른 에너지 준위 변화를 광학적으로 읽어 자기장을 측정한다.|원자종·증기셀·광펌핑·주파수와 충돌 완화·자기장 환경을 제어한다.|스핀 이완, 광시프트와 환경 잡음이 한계이며 각 방식마다 동작 자계·온도 조건이 다르다.|자기장;준비된 원자 스핀>광학·주파수 신호|회전자기비;스핀 이완 시간;광출력;셀 온도|미약 자기장 측정;생체자기 연구;항법 연구|quantum|ωL=γB :: 단순한 라머 세차 관계; 해당 준위·바이어스에서 유효 γ 사용
nv-center-sensing|다이아몬드 NV 중심 감지|NV-center sensing|다이아몬드의 질소-공공 결함 스핀 준위가 자계 등에 따라 변하며, 광학 검출 자기공명으로 변화를 읽는다.|적절한 결함 밀도·스핀 제어, 광 여기 및 마이크로파 판독이 필요하다.|온도·응력·전기장도 공명에 영향을 주므로 자계 변화와 분리해야 한다. 광수집·표면 잡음이 감도를 제한한다.|자기장 등 환경 변화;광·마이크로파>스핀 공명·형광 변화|공명 선폭;광자 수;스핀 결맞음;결함 깊이|미세 자기장 영상;재료 분석;양자 센싱|quantum|-
''',industries='센서;반도체·전자;의료·바이오 연구;정밀기계;통신')

add('ELECTRIC','''
electromagnetic-induction|전자기 유도|Electromagnetic induction|폐회로에 쇄교하는 자속이 시간에 따라 변하면 기전력이 생긴다. 유도 전류는 원인 변화를 방해하는 방향으로 작용하여 에너지 보존과 일관된다.|자속의 시간 변화 또는 회로의 적절한 상대 운동과 전기적 경로가 필요하다.|영구자석이 고정되어 있다는 사실만으로 지속적인 전력이 생기지 않는다. 부하를 연결하면 기계적·전기적 반작용과 손실이 나타난다.|자속 변화>유도 기전력|권선수;자속;변화율;회로 임피던스|발전기;변압기;유도 센서|faraday|ε=−N dΦ/dt :: 각 권선에 같은 자속이 쇄교하는 코일
capacitive-energy-storage|정전용량 에너지 저장|Capacitive energy storage|분리된 전극에 반대 전하를 축적하여 전기장에 에너지를 저장한다. 회로를 통해 충·방전 속도를 조절한다.|유전체의 내전압과 누설, 전극 구조 및 회로 저항을 고려한다.|에너지 밀도·누설·유전체 손실과 절연 파괴가 한계다. 정전용량이 전압에 따라 변하면 상수 C 식을 그대로 쓰지 않는다.|전기 에너지;전하 분리>전기장 에너지;전하 방출|정전용량;전압;ESR;누설|펄스 전원;필터;순간 에너지 완충|capacitor|U=CV²/2 :: 전압에 무관한 선형 정전용량의 저장 에너지
pn-rectification|PN 접합 정류|PN-junction rectification|P형·N형 반도체 접합에 생긴 공핍층과 전위 장벽이 바이어스에 따라 운반자 주입을 비대칭적으로 바꾼다.|도핑·접합 품질과 허용 전압·전류·온도 범위를 지켜야 한다.|역방향 누설과 항복이 존재하며 순방향 전압 강하도 있다. 이상적인 무손실 일방향 밸브가 아니다.|전압;PN 접합>비대칭 전류|도핑;접합 온도;전압;수명|전원 정류;신호 검파;보호 회로|semiconductor|I≈Is[exp(qV/(nkBT))−1] :: 저주입·정상상태의 다이오드 근사; 직렬저항·항복 등은 제외
semiconductor-doping|반도체 도핑|Semiconductor doping|불순물 준위로 전자 또는 정공의 평형 농도를 바꾸어 반도체 전도 특성을 조절한다.|불순물 종류·농도·활성화와 결정 결함, 열 이력을 관리한다.|도핑 증가는 이동도 저하와 재결합·누설 증가를 동반할 수 있다. 모든 불순물이 전기적으로 활성화되는 것은 아니다.|도펀트;반도체>운반자 농도·전도도 제어|농도;활성화율;이동도;온도|트랜지스터;다이오드;저항·센서|doping|σ=q(nμn+pμp) :: 균일 반도체의 선형 수송·저전계 근사
field-effect-transistor|전계 효과 트랜지스터|Field-effect transistor|게이트 전압이 반도체 채널의 운반자 밀도와 전도 경로를 바꾸어 작은 제어 신호로 소스·드레인 전류를 조절한다.|소자 구조에 맞는 게이트 절연·바이어스와 접촉·열 관리를 확보한다.|누설·단채널 효과·기생 용량·자기 발열이 이상 특성을 벗어나게 한다. 증폭 에너지는 외부 전원에서 공급된다.|게이트 전압;전원>채널 전류 제어|문턱전압;이동도;채널 치수;게이트 용량|디지털 논리;전력 스위치;아날로그 증폭|semiconductor|-
superconductivity|초전도 전류 수송|Superconductivity|특정 재료가 임계 조건 아래에서 거시적 양자 상태를 이루어 직류 저항이 사라지는 상태로 전류를 수송한다.|재료별 임계 온도·자기장·전류밀도 범위를 유지해야 한다.|냉각 전력·접합·교류 손실과 퀜치가 남아 있다. 시스템 전체가 무손실이 되는 것은 아니다.|전류;초전도 상태>낮은 직류 손실의 전류 수송|온도;임계전류;자계;안정화재|MRI 자석;가속기;초전도 전력기기|superconductor|-
meissner-effect|마이스너 효과와 자속 배제|Meissner effect|초전도 상태로 전이하면 내부 자기장을 배제하는 차폐 전류가 형성된다. 제2종 초전도체의 혼합 상태에서는 자속 소용돌이가 침투할 수 있다.|재료의 임계 자계·온도 범위와 자속 침투·핀닝 특성을 구분한다.|단순히 저항이 낮은 도체와 동일하지 않다. 모든 자계와 모든 초전도 상태에서 내부 자속이 완전히 0인 것은 아니다.|자기장;초전도 상태>자속 차폐;자기력|온도;자계;침투 깊이;핀닝|자기 차폐;부상 실험;초전도 베어링|superconductor|-
josephson-effect|조지프슨 효과|Josephson effect|두 초전도체 사이의 약한 연결을 통해 위상 차에 의존하는 초전류가 흐르며, 전압은 위상 변화율과 연결된다.|초전도 접합과 저잡음 전기·자기 환경, 냉각이 필요하다.|접합 임계전류와 잡음·자기장에 민감하다. 실제 회로에는 기생 성분과 열 영향이 있다.|초전도 위상 차;접합 전압>초전류;정밀 주파수-전압 변환|임계전류;주파수;접합 용량;온도|전압 표준;SQUID;초전도 회로|quantum-electric|f=2eV/h :: AC 조지프슨 관계; 접합 양단의 전압 V
quantum-hall|양자 홀 효과|Quantum Hall effect|적절한 2차원 전자계가 자기장에서 양자화된 상태를 형성하면 홀 저항에 정밀한 평탄 구간이 나타난다.|재료·운반자 밀도·온도·자기장 및 측정 전류를 양자 홀 평탄 구간에 맞춘다.|모든 도체에서 임의 조건으로 저항이 양자화되지 않는다. 접촉과 누설·소산이 정밀도를 제한한다.|2차원 운반자;자기장>양자화된 홀 저항|충전인자;온도;자계;전류|저항 표준;정밀 전기 계측;전자 물성 연구|quantum-electric|RH=h/(νe²) :: 정수 양자 홀 효과의 이상적인 평탄 구간에서 정수 충전인자 ν
''',industries='반도체·전자;전력;통신;정밀 계측;의료기기;항공우주')

add('HOLD','''
electrostatic-chuck|정전기 척|Electrostatic chuck|전극에 전압을 인가하면 유전체를 사이에 둔 전기장이 대상과 척 사이에 인력을 만든다. 쿨롱형과 유한 전도성을 이용하는 Johnsen–Rahbek형은 접촉 조건이 다르다.|절연층·대상 재질·표면 접촉과 잔류 전하 해제 조건을 관리한다.|일반적인 정전기 척은 표면 접촉을 포함하므로 비접촉 부상과 같지 않다. 누설·절연파괴·잔류 흡착이 문제가 될 수 있다.|전압;전극·유전체;대상>흡착·고정력|전압;유전체 두께;접촉 상태;온도|웨이퍼 고정;진공 공정;박판 취급|esc|p≈εE²/2 :: 이상적인 균일 전계의 전기 압력 척도; 실제 접촉형 척의 힘은 모델별 계산
electrostatic-mems-actuation|정전기 MEMS 구동|Electrostatic MEMS actuation|전극 사이의 전기장 에너지가 형상에 따라 달라져 인력을 만든다. 탄성 복원력과의 균형으로 미세 구조를 움직인다.|전극 간격·탄성 지지·절연과 구동 전압 범위를 설계한다.|당김 불안정인 풀인, 표면 들러붙음, 유전체 충전이 발생할 수 있다. 고정 전압에서도 누설이 있으면 전력 소모가 있다.|전압;가동 전극>미세 변위;구동력|간극;스프링 강성;전압;전극 면적|MEMS 미러;미세 스위치;미세 공진기|capacitor,esc|F≈εAV²/(2g²) :: 균일 평행판·정전압·프린징 무시 근사
''',industries='반도체·전자;디스플레이;정밀기계;광학')

add('ENERGY','''
photovoltaic-conversion|태양광 광기전력 변환|Photovoltaic conversion|반도체가 빛을 흡수해 만든 운반자를 접합의 선택적 접촉과 전기장이 분리·수집하여 전압과 전류를 만든다.|흡수 가능한 광 스펙트럼과 광 입사, 낮은 재결합 손실 및 적합한 부하가 필요하다.|흡수되지 않는 광자, 재결합·열화·온도 상승이 출력을 제한한다. 이름의 정격 출력이 모든 조도에서 나오지는 않는다.|빛>전기 에너지|밴드갭;조도;온도;재결합;부하|태양전지;광전원 센서;우주 전원|solar,semiconductor|P=VI :: 실제 광·온도 조건에서의 I–V 특성과 최대 전력점을 기준으로 사용
regenerative-induction|회생 발전·제동|Regenerative braking|기계가 발전기로 동작할 때 전자기적 반작용 토크로 감속하며 운동·위치 에너지 일부를 전력으로 회수한다.|전력을 받아들일 배터리·DC 링크·계통과 구동 제어가 필요하다.|저속·저장장치 충전 한계·접지 조건에서 회생이 제한된다. 전력 수용부 없이 감속 에너지가 모두 저장되지는 않는다.|기계적 에너지;발전기>전력 회수;제동 토크|속도;토크;전류;저장장치 수용 전력|전기차;엘리베이터;산업 서보|faraday|Pmech=τω :: 축 기계동력; 회수 전력은 변환·배선·저장 손실만큼 작음
piezoelectric-harvesting|압전 진동 에너지 회수|Piezoelectric energy harvesting|외부 진동으로 압전 재료에 생긴 교번 전하를 전기 회로로 추출한다. 기계 공진과 부하 매칭이 회수량에 영향을 준다.|지속적인 기계적 에너지원과 정류·저장 회로, 피로를 견디는 구조가 필요하다.|무부하 고전압이 큰 출력 전력을 뜻하지 않는다. 설치 후 원래 구조의 진동을 바꾸며 대역폭이 제한될 수 있다.|외부 진동>전기 에너지|변형률;주파수;정전용량;부하|무선 센서 전원;구조 감시;소형 에너지 회수|direct-piezo|-
lithium-intercalation|리튬 이온 삽입·탈리 저장|Lithium-ion intercalation storage|리튬 이온이 전해질을 통해 두 전극 사이를 이동하고 전극 내부 저장 상태가 바뀌며, 전자는 외부 회로를 지나 에너지를 교환한다.|전극 전위·전해질 안정 창·온도·전류를 관리하고 이온과 전자의 경로를 분리한다.|전극 손상·부반응·리튬 석출·열폭주 위험이 있다. 전극 조합마다 전압·수명·안전 조건이 다르다.|충전 전력;이온 전도 경로>화학 에너지 저장;방전 전력|전극 조성;SOC;전류밀도;온도|전기차;전자기기;에너지 저장|li-ion,battery|-
electrochemical-cell|전기화학 전지|Electrochemical cell|공간적으로 분리한 산화·환원 반응의 전위 차를 이용해 전자는 외부 회로로, 이온은 전해질로 이동하게 한다.|양극·음극·전해질의 반응성과 전기적·이온적 연속성이 필요하다.|평형 전압이 부하 운전 전압과 같지 않다. 반응 속도·농도 분극·내부 저항과 재료 소모가 출력을 제한한다.|산화·환원 반응물>전류;화학 상태 변화|반응 전위;활성면적;농도;내부 저항|1차전지;충전지;전기화학 센서|battery|ΔG=−nFE :: 가역 전지의 Gibbs 에너지 변화와 평형 기전력 관계
''',industries='에너지;자동차·철도;반도체·전자;산업 자동화;항공우주')

add('RHEO','''
magnetorheological-fluid|자기유변 유체|Magnetorheological fluid|자기장에 의해 자화된 분산 입자가 사슬·기둥형 구조를 형성하여 흐름에 저항한다. 특히 자기장에 따라 항복응력이 변하는 성질을 이용한다.|자성 입자·운반유체와 충분한 자계, 입자 침강 및 열 관리를 고려한다.|단순히 뉴턴 점도가 일정 배수로 증가하는 유체로 설명하면 부정확하다. 자기 포화·침강·마모·온도 변화가 작동을 제한한다.|자기장;자성 현탁액>가변 항복응력;전단 저항|자속밀도;입자 분율;전단률;온도|가변 댐퍼;클러치;촉각 장치|mr|τ≈τy(B)+ηpγ̇ :: 항복 후 양의 전단 방향에서 Bingham형 근사; 이력·속도 의존성은 별도
electrorheological-fluid|전기유변 유체|Electrorheological fluid|전기장에 의해 분극되는 분산계의 미세 구조가 변하면서 항복응력과 유동 저항을 조절한다. 물질 계열에 따라 분극·계면 작용의 지배 기구가 다르다.|입자와 절연성 운반유체의 조합, 전극 간격·전기장·누설 전류를 관리한다.|높은 전기장과 절연파괴·습도·침강에 민감하다. 모든 조성에 같은 전계 지수나 항복응력을 적용하지 않는다.|전기장;현탁액>가변 유동 저항|전계;입자 분율;전도도;수분|가변 밸브;댐퍼;미세 유동 제어|er|-
shear-thinning|전단박화|Shear thinning|고분자 사슬 정렬이나 분산 구조 재배열 등으로 전단률이 증가할 때 겉보기 점도가 감소한다.|측정한 유동 곡선과 온도·조성 범위 안에서 사용한다.|시간에 따른 구조 회복인 틱소트로피와 같은 뜻이 아니다. 전 범위에서 점도가 무한히 감소하는 것은 아니다.|전단 작용>겉보기 점도 감소|전단률;온도;고형분;분자량|사출성형;도료 도포;식품 이송|nonnewtonian|ηapp=Kγ̇^(n−1), n<1 :: 경험적 멱법칙이 맞는 유한 전단률 구간
shear-thickening|전단농화|Shear thickening|고농도 현탁액에서 전단 증가가 입자 간 접촉과 힘 전달 구조를 바꾸어 겉보기 점도를 증가시킬 수 있다.|입도·입자 분율·입자 간 상호작용과 구속 조건이 적절해야 한다.|모든 액체나 모든 충격에서 고체처럼 되는 것은 아니다. 불연속 농화와 재밍, 정상 점도 증가를 구분한다.|전단 작용;농축 현탁액>유동 저항 증가|입자 분율;전단률;입자 마찰;구속|충격 완화 소재;가변 저항층;보호 섬유 연구|rheology|ηapp=Kγ̇^(n−1), n>1 :: 연속 농화의 제한된 구간에만 쓰는 경험식; 재밍은 별도 모델
viscoelastic-response|점탄성|Viscoelasticity|재료가 변형 에너지 일부를 탄성적으로 저장하고 일부는 시간에 따라 소산한다. 응력과 변형의 위상 차가 진동 감쇠로 나타난다.|온도와 시간·주파수 범위에 맞는 저장·손실 탄성률 또는 이완 스펙트럼이 필요하다.|한 주파수에서 얻은 계수를 모든 조건에 적용할 수 없다. 크리프·응력 이완과 장기 처짐을 함께 검토한다.|변형 이력>탄성 복원;에너지 소산|저장 탄성률;손실 탄성률;이완 시간;온도|방진 고무;접착층;폴리머 성형|viscoelastic|G*=G′+iG″ :: 선형 진동 응답의 복소 전단 탄성률; 큰 변형은 별도 모델
''',industries='기계;자동차;고분자·화학;식품;섬유·보호장비')

add('FRICTION','''
mos2-solid-lubrication|이황화몰리브덴 고체 윤활|Molybdenum disulfide solid lubrication|층상 MoS₂ 결정의 기저면 전단과 미끄럼 접촉 중 형성되는 전이막이 접촉부 전단 저항을 줄인다.|코팅 배향·밀착력과 하중·온도·기체 환경을 고려한다.|수분·산화와 마모에 민감하며 환경별 마찰 특성이 다르다. 층상 구조가 없는 DLC와 같은 기구로 설명하지 않는다.|MoS₂ 접촉막;미끄럼>전단 저항·마모 감소|습도;온도;하중;결정 배향|우주 기구;진공 베어링;건식 윤활|mos2|-
dlc-low-friction|DLC 코팅의 저마찰·내마모|Diamond-like carbon tribology|비정질 탄소막의 결합 구조가 높은 경도와 접촉 특성을 만들며, 표면 종결·전이층·환경과의 반응이 마찰에 영향을 준다.|수소 함량과 sp²/sp³ 구성, 기판 밀착력·상대재·윤활 환경을 맞춘다.|DLC는 한 종류의 물질이 아니며 MoS₂처럼 층간 미끄럼만으로 설명할 수 없다. 습도·온도·상대재에 따라 마찰이 크게 변한다.|DLC 표면;미끄럼 접촉>마모 억제;조건부 마찰 감소|막 조성;잔류 응력;상대재;환경|자동차 부품;금형;정밀 기구|solid-lubrication|-
leidenfrost-film|라이덴프로스트 증기막|Leidenfrost vapor film|뜨거운 표면과 액체 사이에서 빠르게 생성된 증기가 액체를 지지하는 막을 형성하여 직접 접촉을 줄인다.|표면·액체·압력에 따른 막비등 조건을 넘고 지속적인 증기 생성이 가능해야 한다.|열전달을 촉진하기보다 단열성 증기막으로 줄일 수 있다. 임계 온도는 고정 상수가 아니며 유체 소모와 안정성 제약이 있다.|고온 표면;액체>증기막;접촉 감소|표면 온도;압력;거칠기;액적 크기|고온 액적 이송 연구;퀜칭 해석;열유체 실험|leidenfrost|-
''',industries='기계;자동차;항공우주;진공;금속·열처리')

add('SURFACE','''
lotus-superhydrophobicity|연잎형 초발수 표면|Lotus-type superhydrophobicity|낮은 표면 에너지와 미세·나노 거칠기가 물방울과 고체의 실제 접촉을 줄이고 공기층을 유지하면 물방울이 쉽게 굴러갈 수 있다.|높은 정적 접촉각뿐 아니라 낮은 접촉각 이력·구름각과 공기층 안정성을 확보한다.|압력·충격·결로·오염·마모로 젖음 상태가 바뀔 수 있다. 물에 대한 발수성이 기름이나 모든 오염물 반발을 뜻하지 않는다.|미세 구조;낮은 표면 에너지;물방울>발수;조건부 자가세정|거칠기;고체 접촉률;접촉각 이력;압력|건축 외장;섬유;응축수 관리 연구|lotus|-
lubricant-infused-surface|윤활액 함침 표면|Lubricant-infused surface|미세 구조에 안정적으로 유지된 윤활액이 매끄러운 액체 계면을 만들어 오염 액적의 접촉선 고정과 부착을 줄인다.|윤활액이 기판을 잘 적시고 처리 액체와의 혼합·치환에 저항해야 한다.|전단에 의한 윤활액 손실과 액적 피복·추출이 수명을 제한한다. 모든 유체 조합에서 성립하는 것은 아니다.|다공 구조;윤활액>낮은 액적 부착;미끄러운 표면|젖음 선택성;윤활액 점도;기공 크기;전단|방오 코팅;유체 취급;응축 표면|slips|-
gecko-dry-adhesion|도마뱀 발형 건식 접착|Gecko-inspired dry adhesion|미세 섬유와 끝단 구조가 표면에 순응하여 실제 접촉 면적을 늘리고 분자 간 힘의 합으로 접착한다. 하중 방향과 박리 방향으로 부착·해제를 조절한다.|충분한 표면 접촉과 적절한 예압·전단 방향, 섬유 강성·형상이 필요하다.|거친 표면·오염·섬유 뭉침이 성능을 제한한다. 진공 흡착과 같은 원리나 모든 표면에서 동일한 접착력은 아니다.|섬유 구조;접촉·전단>가역 부착;방향성 박리|섬유 치수;예압;표면 거칠기;하중 각도|벽면 이동 로봇;재사용 그리퍼;민감 부품 취급|gecko|-
wetting-control|계면 에너지와 젖음성 제어|Wetting control|고체·액체·기체 계면 에너지의 균형이 평형 접촉각에 영향을 준다. 표면 화학이나 구조를 바꾸어 퍼짐·부착을 조절한다.|접촉 액체의 조성과 표면 청정도, 거칠기·화학 균일성을 확인한다.|거친 표면·동적 접촉선·이력에서는 하나의 평형 접촉각만으로 거동을 예측하기 어렵다.|표면 처리;액체>접촉각;퍼짐성 변화|계면장력;거칠기;접촉각 이력;오염|인쇄;도장;접착;미세유체|wetting|γSV−γSL=γLV cosθ :: 평탄·균질·평형 표면의 Young 관계
''',industries='표면처리;건축;섬유;로봇;식품·포장;바이오 소재')

add('FLOW','''
capillary-wicking|모세관 침투·위킹|Capillary wicking|젖음성 계면의 곡률이 압력차를 만들고 점성 저항을 이기면 액체가 작은 관이나 다공성 경로로 침투한다.|액체가 표면을 적시는 조건과 기체 배출, 연결된 공극이 필요하다.|중력·증발·점성 손실·접촉선 고정이 침투 거리와 속도를 제한한다. 모세관 반경 감소가 항상 빠른 유동을 뜻하지 않는다.|젖는 액체;미세 공극>수동 액체 수송|공극 반경;접촉각;표면장력;점도|종이 진단칩;섬유 흡수;히트파이프 심지|capillary|ΔPcap≈2γcosθ/r :: 원형 모세관의 단순 곡률 근사; 침투 속도는 점성·중력 항 포함
''',industries='섬유;진단기기;종이;열관리;농업')

add('HOLD','''
electromagnetic-suspension|전자석 흡인형 자기부상|Electromagnetic suspension|전자석과 자성 궤도·대상 사이 인력이 중력 등 외력을 상쇄한다. 간극 변화에 따른 불안정성을 센서와 전류 제어로 보정한다.|간극 계측·빠른 폐루프 제어·전원과 적합한 자성 경로가 필요하다.|정적 영구자석의 인력만 배치하면 자동 안정 부상이 된다고 가정할 수 없다. 전원 상실과 자성 포화·발열을 검토한다.|전류;자기회로;피드백>비접촉 하중 지지|공극;전류;자속;제어 대역폭|자기부상 교통;능동 자기베어링;비접촉 이송|maglev|-
electrodynamic-suspension|유도 반발형 자기부상|Electrodynamic suspension|자기장과 도체의 상대 운동이 유도 전류를 만들고 그 반작용 자기력이 부상·안내에 기여한다.|충분한 상대 속도 또는 시간 변화 자계와 적합한 도전 경로가 필요하다.|수동 유도 방식은 저속에서 부상력이 부족할 수 있다. 유도 항력·발열과 궤도 구조를 고려한다.|변화하는 자속;도체>반작용 자기력;부상|속도;자계;도체 저항;간극|자기부상 수송;자기 베어링 연구;비접촉 지지|maglev,eddy|-
''',industries='철도;정밀기계;에너지;산업 이송')

add('SHAPE','''
shape-memory-alloy|형상기억 합금|Shape-memory alloy|마르텐사이트와 오스테나이트 사이의 가역 상변태를 이용해 변형 후 가열 시 미리 설정한 형상으로 회복한다.|합금의 변태 온도와 열처리, 허용 변형·응력 및 냉각 경로를 알아야 한다.|일반적인 단방향 효과는 냉각만으로 원래 변형 상태로 되돌아가지 않아 바이어스 하중 등이 필요하다. 피로·히스테리시스·응답 속도가 한계다.|온도 변화;변형된 합금>형상 회복;구동력|변태 온도;응력;변형률;열주기|온도 구동 밸브;소형 액추에이터;전개 구조|sma|-
thermal-expansion-compensation|양·음 열팽창 상쇄|Thermal-expansion compensation|서로 다른 열팽창 특성의 요소를 기하학적으로 연결해 목표 방향의 길이 변화를 상쇄한다.|실제 온도 범위에서 팽창계수와 접합부·형상 치수가 맞아야 한다.|0에 가까운 유효 팽창은 설계한 방향과 범위에 한정된다. 온도 구배·재료 이력·구속 응력은 남는다.|온도 변화;이종 팽창 요소>유효 열변형 감소|팽창계수;길이비;강성;온도 구배|망원경;정밀 프레임;주파수 기준 구조|nte|ΔLnet≈ΣsiαiLiΔT :: 작은 변형·같은 온도 변화의 직렬 기하 근사; si는 연결 방향 부호
''',industries='항공우주;정밀기계;의료기기;자동화')

add('SHAPE','''
auxetic-geometry|음의 푸아송비 구조|Auxetic geometry|오목 셀·회전 단위 등의 기하학적 운동으로 인장 방향뿐 아니라 횡방향도 팽창하는 유효 거동을 만든다.|구조의 변형 모드와 방향, 접합부·재료 탄성 범위를 설계한다.|음의 푸아송비가 모든 방향·변형률에서 일정하거나 자동으로 높은 강도를 뜻하지는 않는다. 좌굴·파손을 검토한다.|축방향 변형;셀 구조>횡방향 동시 팽창|셀 각도;연결부 강성;상대밀도;변형률|보호 구조;형상 가변 패널;필터 기공 제어|auxetic|νeff=−εtrans/εaxial :: 지정한 하중 방향과 변형 범위에서 측정한 유효 푸아송비
bistable-structure|쌍안정 구조|Bistable structure|기하학적 비선형성으로 탄성 에너지에 두 안정 상태를 만들고 임계 하중을 넘으면 다른 상태로 전환되게 한다.|두 상태의 안정성과 전환 장벽, 제조 오차·잔류 응력을 평가한다.|스냅스루 충격과 피로가 생길 수 있으며 임의의 중간 위치를 무전력으로 유지하는 구조는 아니다.|임계 구동 하중>상태 전환;형상 유지|에너지 장벽;곡률;두께;예변형|무전력 래치;전개 구조;기계적 기억|bistable|-
''',domain='GEOMETRIC',industries='건설;항공우주;로봇;섬유·보호장비;기계')

add('FORM','''
diffusion-bonding|확산 접합|Diffusion bonding|고온에서 접촉면의 원자 이동과 변형으로 미세 공극을 줄이고 계면을 가로지르는 금속 결합을 형성한다.|재료 조합·표면 청정도와 충분한 온도·압력·유지 시간이 필요하다.|모재 전체를 녹이는 접합이 아니다. 산화막·취성 반응층·고온 변형과 장시간 공정이 제약이다.|열;압력;청정 접촉면>고상 접합|온도;압력;시간;표면 상태|열교환기;항공 부품;이종재료 접합|diffusion-bond|-
friction-stir-welding|마찰교반 용접|Friction stir welding|회전 공구가 재료를 마찰·소성 변형으로 연화시키고 교반·압착하여 접합부를 만든다. 일반적으로 모재의 벌크 용융 없이 진행한다.|공구·모재 조합과 회전·이송 속도, 축력 및 지지 고정구가 필요하다.|미접합·터널 결함·공구 마모와 잔류 응력 등을 점검한다. 모든 재료가 같은 공구·조건으로 접합되는 것은 아니다.|회전 공구;축력;접합 대상>고상 접합|회전속도;이송속도;축력;공구 형상|알루미늄 차체;철도;항공;배터리 하우징|fsw|-
atomic-layer-deposition|원자층 증착|Atomic layer deposition|표면 활성 자리에 반응하는 전구체를 순차 공급하고 잔여물을 제거하여 자기제한 표면 반응을 반복한다. 사이클 수로 박막 성장을 조절한다.|전구체·기판·온도가 적합하고 충분한 노출·퍼지가 이루어져야 한다.|한 사이클이 항상 정확한 원자 한 층은 아니다. 핵생성 지연·고종횡비 확산·불순물·느린 처리량이 한계다.|전구체 펄스;활성 표면;열 또는 플라스마>등각 박막|온도;노출량;퍼지 시간;사이클 수|반도체 게이트막;배터리 코팅;보호 박막|ald|-
photolithography|광리소그래피|Photolithography|광학계가 패턴을 감광막에 전달하고 노광에 따른 용해도 변화와 현상으로 공간 패턴을 만든다.|파장·개구수·레지스트·초점·노광량·현상 조건과 정렬을 제어한다.|회절·광자 통계·레지스트 화학·결함이 해상도와 재현성을 제한한다. 설계 노드 이름을 실제 모든 선폭으로 해석하지 않는다.|패턴 광;감광막>미세 패턴|파장;개구수;노광량;초점;현상|반도체;MEMS;미세광학;바이오칩|lithography|CD≈k₁λ/NA :: 광리소그래피 해상도의 경험적 Rayleigh 관계; k₁은 공정·패턴에 의존
''',industries='반도체·전자;금속;항공우주;자동차;배터리')

def main():
    catalog=[{'function_ko':name,'effects':effects} for name,effects in groups.items()]
    ids=[e['id'] for g in catalog for e in g['effects']]
    assert len(ids)==len(set(ids))
    DEST.write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'Authored {len(ids)} scientific effects across {len(catalog)} functions')

if __name__=='__main__':main()
