## TSDQ

<div align="center">

<img align='right' src="https://github-readme-stats.vercel.app/api?username=betomsales&show_icons=true&title_color=2E86AB&text_color=A23B72&icon_color=F18F01&bg_color=F7F7F7&hide_border=true&cache_seconds=2300" alt="Estatísticas do GitHub" width="400">

### 👋 Olá, meu nome é Beto!

<img src="https://img.shields.io/static/v1?label=Overview&message=Beto&color=2E86AB&style=for-the-badge&logo=GitHub&labelColor=F7F7F7&logoColor=2E86AB" alt="GitHub Overview">

</div>

---

<p align="justify">
Sou bolsista do <strong>Grupo de Redes Elétricas Inteligentes (GREI)</strong> da UFC - Fortaleza, 
onde atuo no time de <strong>Qualidade de Energia</strong>. Minha pesquisa envolve análise de 
sistemas elétricos, simulações com OpenDSS e desenvolvimento de ferramentas para monitoramento 
e melhoria da qualidade de energia.
</p>

---

<div align="center">

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![OpenDSS](https://img.shields.io/badge/OpenDSS-008000?style=for-the-badge&logo=lightning&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-3F4F75?style=for-the-badge&logo=plotly&logoColor=white)

![Git](https://img.shields.io/badge/Git-F05032?style=for-the-badge&logo=git&logoColor=white)
![GitHub](https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white)
![VS Code](https://img.shields.io/badge/VS_Code-007ACC?style=for-the-badge&logo=visual-studio-code&logoColor=white)

</div>

---

Aqui você encontrará os passos para poder rodar a simulação da qualidade de dados de energia no seu computador!

Antes de mais nada se você é novo por aqui, seja bem-vindo(a)! Para uma melhor compreensão de como realizar uma simulação local (no seu computador) de um repositório (arquivo no GitHub) basta entender que você irá fazer uma cópia desse arquivo (clonar) na sua máquina. Além disso, essa cópia será realizada através de comandos, assim como criar arquivos na área de trabalho. Não precisa de desesperar, basta seguir os passos abaixo! **;D** 

---

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

> **OBS:** Se você possui antivírus no seu computador é normal que ele vasculhe o programa ou até mesmo o Firewall pode solicitar permissão para que o código rode. Então não se preocupe com vírus!

**6.** Rode a simulação.

```bash
  tsdq
```

**7.** Pare a simulação.

Basta apertar o comando Ctrl + C.

<div align="center">
  <a target="_blank" href="https://github.com/grei-ufc" style="background:none">
    <img src="https://github.com/grei-ufc/tsdq-dataview-opentes/blob/main/imagens/Grei2.png?raw=true">
  </a>
</div>
