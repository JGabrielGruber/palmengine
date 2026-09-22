/**
 * Portal paint skins (dogfood). Exact English → locale. Missing key stays English.
 * Paint only: chrome, action.label, choice labels, questions/hints.
 * Never translate value, alias, path, or ids — those stay on the wire.
 */
(() => {
  const EN_CHROME = {
    brand: "Palm Portal",
    documentTitle: "Palm Portal — Assist",
    fabTitle: "Open Palm Portal",
    statusDisconnected: "disconnected",
    statusConnecting: "connecting…",
    statusConnected: "connected",
    statusError: "error",
    menu: "Menu",
    menuTitle: "Palm menu",
    start: "Start",
    minimize: "Minimize",
    find: "Find",
    send: "Send",
    searchMenu: "Search this menu…",
    searchSection: "Search {section}…",
    typeAnswer: "Type an answer…",
    thinking: "Palm is thinking…",
    waitingResponse: "Waiting for response",
    sessionWord: "session",
    instanceWord: "instance",
    flowWord: "flow",
  };

  const EN_SECTIONS = {
    root: "root",
    flows: "flows",
    waiting: "waiting",
    scenarios: "scenarios",
    datasets: "datasets",
  };

  window.PALM_PORTAL_SKINS = {
    en: {
      name: "English",
      blurb: "Open the portal in English",
      chrome: EN_CHROME,
      sections: EN_SECTIONS,
      paint: {},
      prefixes: [],
      synonyms: {},
    },
    "pt-BR": {
      name: "Português (Brasil)",
      blurb: "Abrir o portal em português",
      chrome: {
        brand: "Portal Palm",
        documentTitle: "Portal Palm — Assist",
        fabTitle: "Abrir o Portal Palm",
        statusDisconnected: "desconectado",
        statusConnecting: "conectando…",
        statusConnected: "conectado",
        statusError: "erro",
        menu: "Menu",
        menuTitle: "Menu Palm",
        start: "Começar",
        minimize: "Minimizar",
        find: "Buscar",
        send: "Enviar",
        searchMenu: "Buscar neste menu…",
        searchSection: "Buscar {section}…",
        typeAnswer: "Escreva uma resposta…",
        thinking: "Palm está pensando…",
        waitingResponse: "Aguardando resposta",
        sessionWord: "sessão",
        instanceWord: "instância",
        flowWord: "fluxo",
      },
      sections: {
        root: "início",
        flows: "fluxos",
        waiting: "esperando",
        scenarios: "cenários",
        datasets: "conjuntos",
      },
      prefixes: [
        ["Finished. Answers: ", "Concluído. Respostas: "],
        ["Waiting on ", "Aguardando "],
        ["Ready to start ", "Pronto para começar "],
        ["Tap Start ", "Toque em Começar "],
        ["Menu · ", "Menu · "],
        ["Searching ", "Buscando "],
        ["Search: ", "Busca: "],
        ["Palm ", "Palm "],
      ],
      synonyms: {
        sim: "yes",
        nao: "no",
        sair: "exit",
        pronto: "done",
        pular: "skip",
        adicionar: "add",
        editar: "edit",
        remover: "remove",
        amigo: "friend",
        estranho: "stranger",
        encrenca: "trouble",
        rumores: "rumors",
        comercio: "trade",
        "ir embora": "leave",
        "sobre ela": "about",
        comprar: "buy",
        mais: "more",
        baixa: "low",
        media: "medium",
        alta: "high",
        comecar: "start",
        iniciar: "start",
      },
      paint: {
        // chrome / sys
        "Connected to Palm Assist": "Conectado ao Assist Palm",
        Disconnected: "Desconectado",
        "Not connected": "Não conectado",
        "Invalid frame from server": "Quadro inválido do servidor",
        "Starting…": "Começando…",
        "Starting operator entry…": "Abrindo a entrada do operador…",
        "Opening Palm menu…": "Abrindo o menu Palm…",
        "Session bound": "Sessão vinculada",
        "Walk cleared": "Caminho limpo",
        "Running resource step…": "Executando o passo de recurso…",
        "Session finished": "Sessão concluída",
        "Resource running…": "Recurso em execução…",
        "Pick a row, or search above…": "Escolha uma linha, ou busque acima…",
        "More rows available — use Show more":
          "Há mais linhas — use Mostrar mais",
        "Or type a choice value…": "Ou digite o valor da escolha…",
        "yes / no": "sim / não",
        Yes: "Sim",
        No: "Não",
        Skip: "Pular",
        Action: "Ação",
        action: "ação",
        "Search (clear)": "Busca (limpar)",
        "Search this menu…": "Buscar neste menu…",
        "Search menu…": "Buscar no menu…",
        "Type an answer…": "Escreva uma resposta…",
        "Optional — type or Skip": "Opcional — digite ou Pule",
        "Optional — type a value or Skip": "Opcional — digite um valor ou Pule",
        "Enter value…": "Digite o valor…",
        "add / done / item text…": "adicionar / pronto / texto do item…",
        "Palm is thinking…": "Palm está pensando…",
        "Waiting for response": "Aguardando resposta",

        // operator-entry
        "What would you like to do with Palm? Run a demo flow (todo, compositional, coconut NPC with KV resources), design a flow/resource, or inspect the catalog.":
          "O que você gostaria de fazer com o Palm? Rodar um fluxo de demonstração (tarefas, composto, NPC Coconut com recursos KV), desenhar um fluxo/recurso, ou inspecionar o catálogo.",
        "Read-only catalog mode. Say exit when done.":
          "Modo catálogo só-leitura. Diga sair quando terminar.",
        "Read-only catalog mode. Use actions to inspect flows, propose a new flow, or list waiting sessions. Say exit when done.":
          "Modo catálogo só-leitura. Use as ações para inspecionar fluxos, propor um fluxo novo, ou listar sessões à espera. Diga sair quando terminar.",
        "Todo Builder": "Lista de tarefas",
        "Compositional Parent": "Fluxo composto",
        "Coconut Npc": "Coconut (NPC)",
        "Create Flow": "Criar fluxo",
        "Improve Flow": "Melhorar fluxo",
        "Propose Resource": "Propor recurso",
        "Inspect Only": "Só inspecionar",
        "Ready to start Todo Builder.": "Pronto para começar a lista de tarefas.",
        "Ready to start Compositional Parent.":
          "Pronto para começar o fluxo composto.",
        "Ready to start Coconut NPC.": "Pronto para começar Coconut (NPC).",
        "Tap Start Todo Builder (or say start) to begin.":
          "Toque em Começar Lista de tarefas (ou diga começar) para iniciar.",
        "Tap Start Compositional Parent (or say start) to begin.":
          "Toque em Começar Fluxo composto (ou diga começar) para iniciar.",
        "Tap Start Coconut NPC (or say start) to begin.":
          "Toque em Começar Coconut (NPC) (ou diga começar) para iniciar.",
        "Say handoff or start to open your flow.":
          "Diga entregar ou começar para abrir o fluxo.",

        // actions (labels only)
        "Start operator entry": "Começar entrada do operador",
        "Start Todo Builder": "Começar lista de tarefas",
        "Start Compositional Parent": "Começar fluxo composto",
        "Start Coconut NPC": "Começar Coconut (NPC)",
        "Start coconut NPC": "Começar Coconut (NPC)",
        "Hand off to business flow": "Entregar ao fluxo de negócio",
        "Browse all flows": "Ver todos os fluxos",
        "Browse flows": "Ver fluxos",
        "Palm menu": "Menu Palm",
        "List flows": "Listar fluxos",
        "List waiting sessions": "Listar sessões à espera",
        "Publish new flow (one call)": "Publicar fluxo novo (uma chamada)",
        "Publish flow change (one call)": "Publicar mudança de fluxo (uma chamada)",
        "Publish resource (one call)": "Publicar recurso (uma chamada)",
        "Publish missing resource": "Publicar recurso ausente",
        "Doctor (resource preflight)": "Doctor (pré-voo do recurso)",
        "Inspect this session": "Inspecionar esta sessão",
        "Exit catalog": "Sair do catálogo",
        "Send answer": "Enviar resposta",
        "Go back": "Voltar",
        "Resume session": "Retomar sessão",
        "Cancel session": "Cancelar sessão",
        "Run again": "Rodar de novo",
        "Resume resource step": "Retomar passo de recurso",
        "Open child session": "Abrir sessão filha",
        "Run flow": "Rodar fluxo",
        Resume: "Retomar",
        Publish: "Publicar",
        Doctor: "Doctor",
        "Show more": "Mostrar mais",
        "Menu home": "Início do menu",
        "Operator entry": "Entrada do operador",
        "Design entry": "Entrada de desenho",
        "Admission (starts closed)": "Admissão (começa fechada)",
        "Continue answering": "Continuar a responder",
        "Query table": "Consultar tabela",
        "Query series": "Consultar série",
        "Analytics datasets": "Conjuntos de analytics",
        Flows: "Fluxos",
        "Waiting sessions": "Sessões à espera",
        "Assist scenarios": "Cenários Assist",
        "Browse and run catalog flows": "Ver e rodar fluxos do catálogo",
        "Sessions waiting for input": "Sessões à espera de resposta",
        "Operator entry, design entry, …": "Entrada do operador, entrada de desenho, …",
        "Published resources for AnalyticsService":
          "Recursos publicados para AnalyticsService",
        "Guided triage menu": "Menu guiado de triagem",
        "Create / improve flow or resource": "Criar / melhorar fluxo ou recurso",
        "Engine health": "Saúde do motor",

        // assist hints
        "Reply with a number or choice name.":
          "Responda com um número ou o nome da escolha.",
        "Reply with your answer.": "Responda com a sua resposta.",
        "Reply yes or no.": "Responda sim ou não.",
        "Say add, edit, remove, or done.":
          "Diga adicionar, editar, remover ou pronto.",
        "Optional — enter a value, or Skip / leave empty.":
          "Opcional — digite um valor, ou Pule / deixe vazio.",
        "Pick a choice or type a value.":
          "Escolha uma opção ou digite um valor.",
        "Enter text for this item.": "Digite o texto deste item.",
        "Reply with item number or label.":
          "Responda com o número ou o rótulo do item.",
        "Resource step auto-runs — wait, or use Resume resource step if stuck.":
          "O passo de recurso roda sozinho — espere, ou use Retomar passo de recurso se travar.",
        "Resource failed — try Resume or Doctor.":
          "O recurso falhou — tente Retomar ou Doctor.",
        "Complete the wait target; this session unparks automatically.":
          "Conclua o alvo da espera; esta sessão despausa sozinha.",
        "Flow finished successfully.": "Fluxo concluído com sucesso.",
        "Flow failed.": "O fluxo falhou.",
        "Session complete — start another flow or return to operator entry.":
          "Sessão concluída — comece outro fluxo ou volte à entrada do operador.",
        "Session complete — no further input.":
          "Sessão concluída — sem mais respostas.",
        "Inspect the session or start a new run.":
          "Inspecione a sessão ou comece uma nova execução.",
        "Ready to hand off — call assist session handoff or choose continue.":
          "Pronto para entregar — chame o handoff da sessão ou escolha continuar.",
        "Which item?": "Qual item?",
        "Inspect catalog: use read/design-discovery actions only; send exit when the user is done.":
          "Inspecionar catálogo: use só ações de leitura/descoberta; envie sair quando a pessoa terminar.",
        "No business flow handoff. One call: palm_design_publish_flow(body=…).":
          "Sem entrega a fluxo de negócio. Uma chamada: palm_design_publish_flow(body=…).",
        "No business flow handoff. One call: palm_design_publish_flow(base_flow_id=…, body=…).":
          "Sem entrega a fluxo de negócio. Uma chamada: palm_design_publish_flow(base_flow_id=…, body=…).",
        "No business flow handoff. One call: palm_design_publish_resource(body=…).":
          "Sem entrega a fluxo de negócio. Uma chamada: palm_design_publish_resource(body=…).",
        "No business flow handoff. Catalog inspect complete.":
          "Sem entrega a fluxo de negócio. Inspeção do catálogo concluída.",
        "One call: palm_design_publish_flow(body={name, pattern, options.steps}). Handoff optional.":
          "Uma chamada: palm_design_publish_flow(body={name, pattern, options.steps}). Entrega opcional.",
        "One call: palm_design_publish_flow(base_flow_id=…, body=…). Handoff optional.":
          "Uma chamada: palm_design_publish_flow(base_flow_id=…, body=…). Entrega opcional.",
        "One call: palm_design_publish_resource(body={name, provider, action, …}). Flows like coconut-npc need kv resources registered first.":
          "Uma chamada: palm_design_publish_resource(body={name, provider, action, …}). Fluxos como coconut-npc precisam dos recursos kv registrados antes.",
        "Handoff returns kind=design — use palm_design_* tools (or re-enter via actions).":
          "A entrega devolve kind=design — use as ferramentas palm_design_* (ou volte pelas ações).",

        // todo-builder
        "Build a todo list. On finish, Palm persists the list to kv (palm-todos). Priority analytics is a virtual view at query time.":
          "Monte uma lista de tarefas. Ao terminar, o Palm grava a lista no kv (palm-todos). A análise de prioridade é uma vista virtual na consulta.",
        "Manage your todos — add items, edit/remove, then continue.":
          "Gerencie as tarefas — adicione itens, edite/remova, depois continue.",
        "What needs to be done?": "O que precisa ser feito?",
        "Due date (YYYY-MM-DD, or leave empty to skip)":
          "Prazo (AAAA-MM-DD, ou deixe vazio para pular)",
        "Use YYYY-MM-DD or leave empty": "Use AAAA-MM-DD ou deixe vazio",
        "How urgent is this?": "Qual a urgência?",
        Title: "Título",
        "Due Date": "Prazo",
        Priority: "Prioridade",
        Welcome: "Boas-vindas",
        "Todo List": "Lista de tarefas",
        "Save todos": "Salvar tarefas",
        "Persist list to kv (put-palm-todos)":
          "Gravar a lista no kv (put-palm-todos)",
        Low: "Baixa",
        Medium: "Média",
        High: "Alta",

        // coconut NPC (static prompts + choice labels)
        "*(You approach Coconut's stall — coconuts, rumors, and questionable advice.)*\n\nWhat name do you give?":
          "*(Você se aproxima da barraca da Coconut — cocos, rumores e conselhos duvidosos.)*\n\nQue nome você dá?",
        "What name do you give?": "Que nome você dá?",
        '*(Coconut considers your greeting.)*\n\n"So — friend, stranger, or trouble?"':
          "*(Coconut considera a sua saudação.)*\n\n\"Então — amigo, estranho ou encrenca?\"",
        Friend: "Amigo",
        Stranger: "Estranho",
        Trouble: "Encrenca",
        Rumors: "Rumores",
        Trade: "Comércio",
        About: "Sobre ela",
        Leave: "Ir embora",
        More: "Mais",
        Buy: "Comprar",
        '*(She leans on the cart.)*\n\n"Well then. What\'ll it be?"':
          "*(Ela se apoia no carrinho.)*\n\n\"Bem. O que vai ser?\"",
        '"Good. Friends get the sweet coconuts and the good rumors."':
          '"Ótimo. Amigos levam os cocos doces e os bons rumores."',
        '"Strangers pay full price and get the boring rumors."':
          '"Estranhos pagam o preço cheio e levam os rumores chatos."',
        '"Trouble gets watched. And the coconuts with the soft spots."':
          '"Encrenca fica vigiada. E leva os cocos com parte mole."',
        '"Hmph."': '"Humpf."',
        "*(She grins — she knows your face.)*\n\n\"Welcome back, friend. Rumors, trade, or are you done for today?\"":
          "*(Ela sorri — conhece o seu rosto.)*\n\n\"Bem-vindo de volta, amigo. Rumores, comércio, ou já acabou por hoje?\"",
        "*(She squints, not quite placing you.)*\n\n\"Still a stranger, then. Rumors, trade, or on your way?\"":
          "*(Ela estreita os olhos, sem te situar.)*\n\n\"Ainda um estranho, então. Rumores, comércio, ou seguindo viagem?\"",
        "*(She keeps one hand near the scales.)*\n\n\"Trouble again. Rumors, trade, or walk away while you can?\"":
          "*(Ela deixa uma mão perto da balança.)*\n\n\"Encrenca de novo. Rumores, comércio, ou vai embora enquanto pode?\"",
        '"The jarl\'s steward bought every rope in town — make of that what you will."\n\n"Old Mora says the well water tastes of iron since the last storm."\n\n"Someone left an offering at the shrine at midnight. I didn\'t see who."':
          '"O capataz do jarl comprou toda a corda da vila — tire as suas conclusões."\n\n"A velha Mora diz que a água do poço tem gosto de ferro desde a última tempestade."\n\n"Alguém deixou uma oferenda no santuário à meia-noite. Eu não vi quem."',
        '"Fresh coconuts, two septims. Dried slices for the road, five."\n\n"Pay first. Coconut\'s policy."':
          '"Cocos frescos, dois septims. Fatias secas para a estrada, cinco."\n\n"Paga primeiro. Política da Coconut."',
        "\"A fine choice. Don't drop it on the cobbles — I won't refund dignity.\"\n\n*(You now have a coconut.)*":
          '"Boa escolha. Não deixe cair nas pedras — eu não devolvo dignidade."\n\n*(Agora você tem um coco.)*',
        "\"Name's Coconut. My mother had a sense of humor.\"\n\n\"Twenty years on this road. I know who's lying and who's just ugly.\"\n\n\"Don't ask which you are.\"":
          '"Meu nome é Coconut. Minha mãe tinha senso de humor."\n\n"Vinte anos nesta estrada. Eu sei quem mente e quem é só feio."\n\n"Não pergunte qual você é."',
        '"Safe roads, traveler. And if the bells ring twice at dawn — don\'t look back."\n\n*(Coconut returns to arranging her wares.)*':
          '"Boas estradas, viajante. E se os sinos tocarem duas vezes ao amanhecer — não olhe para trás."\n\n*(Coconut volta a arrumar as mercadorias.)*',
        " I remember you.": " Eu lembro de você.",

        // compositional parent
        "Run nested-composition child wizard?":
          "Rodar o assistente-filho nested-composition?",
        "Orchestrate Child Flows": "Orquestrar fluxos filhos",
      },
    },
  };
})();
