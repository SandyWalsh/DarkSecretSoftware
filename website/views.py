from django.shortcuts import render_to_response

def home(request):
    return render_to_response('index.html', {})

def help(request, cmds):
    return "Commands: %s" % ', '.join(cmds.keys())

CMDS = {
    'help': help,
    '?': help,
}

def query(request):
    text = request.POST.get('query', "").lower()
    response = "Syntax Error"
    if text in CMDS:
        response = CMDS[text](request, CMDS)
    return render_to_response('query.html', {'text': response})
