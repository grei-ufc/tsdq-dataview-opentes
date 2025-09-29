## TSDQ

[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Grei](https://img.shields.io/badge/-GREI-Black?logo=INSPIRE&logoColor=blue&color=42b85a&labelColor=white&style=flat)](https://www.linkedin.com/company/grei-ufc/?originalSubdomain=br)
[![image](https://img.shields.io/badge/-Python%20Version%20|%203.12.11-42b85a?logo=Python&logoColor=fbec41&color=42b85a&labelColor=grey&style=flat)](https://www.python.org/downloads/release/python-31112/)
[![Discord](https://img.shields.io/badge/Discord-%235865F2.svg?logo=discord&logoColor=white)](https://discord.com/channels/1415180099644297368/1415431164717564065)

Olá usuário! Aqui você encontrará os passos para poder rodar a simulação da qualidade de dados de energia no seu computador!

Antes de mais nada se você é novo por aqui, seja bem-vindo(a)! Para uma melhor compreensão de como realizar uma simulação local (no seu computador) de um repositório (arquivo no GitHub) basta entender que você irá fazer uma cópia desse arquivo (clonar) na sua máquina. Além disso, essa cópia será realizada através de códigos, assim como criar arquivos (documentos) na área de trabalho. Não precisa de desesperar, basta seguir os passos abaixo! **;D** 
### REQUISITOS INICIAIS
- VSCode ou Git instaldado;
- Conta no GitHub;
- Internet.
    
## Instalação do ``uv``
- Lembre-se de sempre esperar o programa entender o código para que você possa escrever novamente, ele sempre fará uma chamada de código para que você escreva. **Tenha paciência!** 

- Caso você queira usar o Git Bash, após o download do programa Git basta clicar com o botão direito do mouse na área de trabalho e procurar **"Abrir Git Bash aqui"** ou **"Open Git Bah Here"** (para os gringos). Além disso, não se esqueça, se você for apenas copiar o código e colar não use os comandos CTRL + C e CTRL +V, o Git Bash compreende esse comando como código. Dessa forma, **use sempre o botão direito do mouse para colar**.

**1.** Se você utiliza o Git Bash (recomendado para quem usa VSCode + Git Bash):

```bash
  pip install uv
```

Para conferir se realmente deu certo basta escrever:

```bash
  uv --version
```

**2.** Caso você já tenha feito o passo de abrir o Git Bash na área de trabalho não será necesário utilizar o comando abaixo, mas caso contrário utilize-o, pois ele fará com que você vá direto ao seu Desktop.

```bash
  cd ~/Desktop
```

**3.** Agora vamos clonar (copiar) o repositório completo para uma nova pasta no seu computador. O link do repositório é obtido no lado superior direito em **"Code"**. Como pode ser visto abaixo.

<div align="center">
     <img src="https://github.com/grei-ufc/tsdq-dataview-opentes/blob/main/imagens/Code_HTTP_copy.png?raw=true">
  </a>
</div>

```bash
  git clone https://github.com/grei-ufc/tsdq-dataview-opentes.git
```

**4.** Agora com a pasta já na sua máquina vamos para dentro do arquivo.

```bash
  cd tsdq-dataview-opentes
```

**5.** Instale as dependências (bibliotecas) do projeto no seu computador. Elas podem ser visualizadas pelo **pyproject.toml**.

```bash
  uv sync
```

Isso pode demorar um pouco então espere até a próxima chamada de código... seja paciente! Por fim, agora é só rodar a simulação através do streamlit que é a interface que mostrará os dados do projeto.

**6.** Rode a simulação.

```bash
  uv run streamlit run demo_cigree.py
```
ou 

```bash
  uv run streamlit run demo_1.py
```

**7.** Pare a simulação.

Basta apertar o comando Ctrl + C no próprio Git Bash.

<div align="center">
  <a target="_blank" href="https://github.com/grei-ufc" style="background:none">
    <img src="https://github.com/grei-ufc/tsdq-dataview-opentes/blob/main/imagens/Grei2.png?raw=true">
  </a>
</div>
