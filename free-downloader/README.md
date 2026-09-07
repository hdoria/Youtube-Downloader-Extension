# Free Video Downloader

Extensão Chrome com auxiliar local para baixar vídeos do YouTube, com áudio e qualidade de até 2160p (4K), quando a fonte oferece essa resolução. Sem cobrança e sem servidor próprio. Este diretório contém uma implementação original, independente do código Tubly presente no restante do repositório.

## Instalação no macOS

Requisitos: Chrome 105 ou superior, Python 3.10 ou superior, FFmpeg e Node.js. O auxiliar usa yt-dlp. Se você usa Homebrew:

```sh
brew install python ffmpeg node
```

1. Abra `chrome://extensions`, ative **Modo do desenvolvedor** e clique em **Carregar sem compactação**.
2. Selecione a pasta `free-downloader/extension` deste repositório.
3. Copie o ID da extensão exibido pelo Chrome.
4. No terminal, dentro da raiz deste repositório, execute o comando abaixo, substituindo `ID_DA_EXTENSAO`:

```sh
python3 free-downloader/native/install_macos.py ID_DA_EXTENSAO
```

O instalador cria um ambiente Python isolado em `~/.local/share/free-video-downloader`, instala/atualiza yt-dlp e registra o auxiliar somente para o ID informado. Não precisa de sudo. O FFmpeg e o Node.js já devem estar instalados.

Abra um vídeo no YouTube, clique na extensão, escolha o limite de qualidade e clique em **Baixar vídeo**. Também é possível colar um link. O arquivo aparece em `~/Downloads/Free Video Downloader`.

## Comportamento

- Um download por vez. O popup pode ser fechado; a conexão Native Messaging permanece no service worker. Mantenha o Chrome aberto até terminar.
- O nome do arquivo inclui o teto solicitado (`max-720p`, `max-2160p` etc.), para uma tentativa anterior em qualidade menor não impedir outra em qualidade maior. O sufixo indica o limite pedido, não a resolução real da fonte.
- A qualidade é um teto pela altura: 2160p, 1440p, 1080p ou 720p. Fontes menores mantêm a resolução original; não há aumento artificial de resolução.
- Vídeo e áudio separados são combinados pelo FFmpeg em MKV, sem recodificação. Vídeos já combinados podem manter MP4 ou WebM. O player precisa suportar os codecs originais, como AV1 ou VP9.
- O progresso é real e corresponde à faixa em download. Pode reiniciar ao passar de vídeo para áudio. A etapa de junção tem mensagem própria.
- Links de vídeos individuais são normalizados; playlists, domínios externos e URLs sem HTTPS são recusados. Não existe modo de login/cookies nesta versão.
- Erros do YouTube, exigências de autenticação, mudanças da plataforma e restrições regionais podem impedir um download. Atualize o auxiliar executando novamente o instalador.
- Encerrar o Chrome ou recarregar a extensão interrompe a conexão. Não há fila persistente nem retomada automática. Uma nova tentativa pode aproveitar partes já baixadas pelo yt-dlp.

## Desenvolvimento e validação

```sh
python3 -m unittest discover -s free-downloader/tests -v
node --test free-downloader/tests/background.test.cjs
node --check free-downloader/extension/background.js
node --check free-downloader/extension/popup.js
```

Os testes verificam validação de URLs, limites de qualidade, enquadramento binário Native Messaging e comunicação com um processo auxiliar, usando um downloader de teste sem rede. Para testar integração real, instale a extensão e o auxiliar, inicie um download, feche o popup, reabra e confira o resultado. A interface no Chrome exige essa verificação manual.

O auxiliar executa yt-dlp por lista de argumentos, sem shell, ignora configurações externas e mantém stdout exclusivo para mensagens JSON com prefixo de tamanho. A extensão pede apenas `activeTab`, `nativeMessaging` e `storage`. Nenhum cookie do navegador é lido.

## Remoção

Remova a extensão em `chrome://extensions`. Para desregistrar o auxiliar, remova o arquivo `~/Library/Application Support/Google/Chrome/NativeMessagingHosts/com.hdoria.free_video_downloader.json` e, se desejar, a pasta `~/.local/share/free-video-downloader`. Os vídeos baixados ficam preservados na pasta Downloads.

## Licença e dependências

Somente o código original deste diretório está sob a [licença MIT](LICENSE). A licença não cobre arquivos do repositório fora deste diretório nem muda os direitos sobre o projeto original. yt-dlp, FFmpeg, Node.js e Python mantêm suas próprias licenças e são instalados separadamente. Baixe conteúdo que você tenha autorização para salvar.

Referências: [Native Messaging do Chrome](https://developer.chrome.com/docs/extensions/develop/concepts/native-messaging), [yt-dlp](https://github.com/yt-dlp/yt-dlp), [FFmpeg](https://ffmpeg.org/).
