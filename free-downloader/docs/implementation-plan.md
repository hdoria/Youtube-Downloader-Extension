# Plano e critérios da primeira versão

Arquitetura aprovada pelo usuário: extensão Chrome original e gratuita com auxiliar local yt-dlp + FFmpeg, permitindo vídeos e áudio até 2160p quando a fonte oferece essa resolução. O plano inicial foi comunicado antes da implementação; este documento registra o escopo para manutenção e revisão.

## Escopo

Somente `free-downloader/`: extensão Manifest V3, auxiliar Python, instalador macOS, documentação, licença MIT para o novo código e testes. O código original do restante do fork não é reutilizado nem relicenciado.

## Etapas

1. Validar URLs individuais do YouTube e limites de qualidade; testar enquadramento Native Messaging e composição de comandos antes de implementar o auxiliar.
2. Executar yt-dlp sem shell e sem configuração externa; juntar vídeo/áudio com FFmpeg; usar Node explicitamente para desafios JavaScript; transmitir progresso real e erros saneados.
3. Manter o Port nativo no service worker para permitir fechar o popup; persistir o estado da sessão e impedir downloads concorrentes.
4. Disponibilizar instalador por usuário, sem sudo e com origem limitada ao ID informado; documentar requisitos e instalação manual no Chrome.
5. Executar testes Python e Node, verificar sintaxe e submeter a revisão independente. A verificação visual real no Chrome permanece manual quando a automação do navegador não permitir instalação.

## Critérios de aceite

- Um vídeo por solicitação, URL HTTPS YouTube validada e altura máxima em 720/1080/1440/2160p, sem upscale.
- Salvar vídeo com áudio em Downloads/Free Video Downloader e preservar arquivos entre limites diferentes de qualidade.
- Sem cobrança, backend remoto próprio, leitura de cookies ou execução de comandos recebidos do navegador.
- Stdout do auxiliar contém apenas JSON com prefixo binário de tamanho; falhas não expõem stack trace ou logs internos.
- Fechar/reabrir popup preserva o job enquanto Chrome e conexão nativa permanecem ativos.
- Testes de protocolo, entrada, seleção de qualidade e ciclo de vida passam. Limitações de teste visual são declaradas.

Condição de parada: código dentro do escopo, testes aprovados, revisão independente tratada e instalação documentada. Publicação, instalação manual no Chrome e empacotamento para loja são etapas separadas.
