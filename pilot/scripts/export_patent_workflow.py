"""Generate n8n's visible subprocess/Gate nodes from the authoring registry."""
import json
from pathlib import Path
from patent_draft.workflow import load_contract


def build():
    contract = load_contract()
    nodes = []
    connections = {}
    def add(id, name, type, position, parameters, version=1, **extra):
        nodes.append(dict(id=id,name=name,type='n8n-nodes-base.'+type,typeVersion=version,
                          position=position,parameters=parameters,**extra))
    def connect(source, targets):
        connections[source]={'main':[[{'node':target,'type':'main','index':0}] for target in targets]}
    def switch(id, name, field, values, position):
        rules=[{'renameOutput':True,'outputKey':v,'conditions':{'options':{'caseSensitive':True,'typeValidation':'strict','version':2},
            'conditions':[{'leftValue':'={{ $json.'+field+' }}','rightValue':v,'operator':{'type':'string','operation':'equals'}}],
            'combinator':'and'}} for v in values]
        add(id,name,'switch',position,{'mode':'rules','rules':{'values':rules},'options':{'fallbackOutput':'extra'}},3.2)
    add('webhook','Patent Dispatch','webhook',[-700,0],{'httpMethod':'POST','path':'patent-dispatch',
        'authentication':'headerAuth','responseMode':'onReceived','options':{}},2,webhookId='patent-dispatch')
    add('input','Dispatch payload','set',[-480,0],{'mode':'raw','jsonOutput':'={{ JSON.stringify($json.body) }}','options':{}},3.4)
    subprocesses=[n for n in contract['nodes'] if n['tool']]
    switch('route','Route issued node','node_id',[n['id'] for n in subprocesses],[-220,0])
    names=[]
    for index,n in enumerate(subprocesses):
        name=n['id']+' · '+n['label']
        names.append(name)
        notes='Inputs: '+', '.join(n['inputs'])+'\nOutputs: '+', '.join(n['outputs'])+'\nMCP: '+n['tool']
        if n.get('prompt'):
            notes+='\nPrompt: prompts/'+n['prompt']+'.md\n\n'+contract['prompts'][n['prompt']]
        add(n['id'],name,'httpRequest',[140+(index//5)*300,(index%5)*240],{
            'method':'POST','url':"={{ $env.TRIZ_API_URL + '/internal/patent/workflow/' + $json.task_id + '/execute' }}",
            'authentication':'genericCredentialType','genericAuthType':'httpHeaderAuth','options':{'timeout':3600000}},4.2,
            retryOnFail=True,maxTries=3,waitBetweenTries=5000,notes=notes,notesInFlow=False)
        connect(name,['Continue or checkpoint'])
    add('continue','Continue or checkpoint','if',[1100,0],{'conditions':{'options':{'caseSensitive':True,'typeValidation':'strict','version':2},
        'conditions':[{'leftValue':'={{ $json.continue_execution }}','rightValue':True,'operator':{'type':'boolean','operation':'true','singleValue':True}}],
        'combinator':'and'},'options':{}},2.2)
    gates=[n for n in contract['nodes'] if n['type']=='gate']
    switch('gates','Gate checkpoint','gate_id',[n['id'] for n in gates],[1340,240])
    gate_names=[]
    for i,n in enumerate(gates):
        name=n['id']+' · '+n['label'];gate_names.append(name)
        add(n['id'],name,'noOp',[1600,i*180],{},notes=n['condition']+'\nResponses resume from the durable DB queue.',notesInFlow=True)
    add('done','Completed or paused','noOp',[1600,760],{})
    add('unknown','Unknown node - operator check','stopAndError',[140,1300],{'errorMessage':'Unknown Patent node ID; no task executed.'})
    connect('Patent Dispatch',['Dispatch payload']);connect('Dispatch payload',['Route issued node'])
    connect('Route issued node',names+['Unknown node - operator check'])
    connect('Continue or checkpoint',['Route issued node','Gate checkpoint'])
    connect('Gate checkpoint',gate_names+['Completed or paused'])
    return {'name':'Patent — stages, Gates and MCP subprocesses','active':False,'nodes':nodes,'connections':connections,
            'settings':{'executionOrder':'v1','executionTimeout':14400,'saveExecutionProgress':True},'pinData':{},'tags':[]}


if __name__=='__main__':
    target=Path(__file__).resolve().parents[2]/'deploy/n8n/patent-workflow.json'
    target.write_text(json.dumps(build(),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(target)
