# 🚀 VisionIA - Sistema de Validação Automática de Screenshots com IA

<div align="center">
[![Logo.jpg](https://i.postimg.cc/wBkRvrt7/Logo.jpg)](https://postimg.cc/SXJx1Dfh)

**Uma plataforma inteligente de pré-validação de screenshots usando visão computacional**

[![MIT License]([![Telade-Login.jpg](https://i.postimg.cc/vZdsNNcq/Telade-Login.jpg)](https://postimg.cc/MvtNct0V))<br/>
[![GitHub Stars](https://img.shields.io/github/stars/RickDevAI/VisionIA?style=social)](https://github.com/RickDevAI/VisionIA/stargazers)<br/>
[![GitHub Forks](https://img.shields.io/github/forks/RickDevAI/VisionIA?style=social)](https://github.com/RickDevAI/VisionIA/network/members)<br/>
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)

[Demo ao Vivo](https://vision-ia-flame.vercel.app) · [Reportar Bug](https://github.com/RickDevAI/VisionIA/issues) · [Solicitar Feature](https://github.com/RickDevAI/VisionIA/issues)
</div>

---

## 📋 Sobre o Projeto

VisionIA é um sistema inteligente de validação automática de screenshots desenvolvido como Trabalho de Conclusão de Curso (TCC). Utiliza visão computacional baseada em YOLOv8 para classificar imagens em três categorias: **PASS** (aprovado), **WARNING** (alerta) e **FAIL** (reprovado), retornando ainda um score de confiança e um comentário gerado em linguagem natural sobre a análise.

O objetivo principal é automatizar o processo de verificação visual de telas de aplicações, documentos digitais ou qualquer conteúdo gráfico que precise estar em conformidade com padrões predefinidos.

### ✨ Principais Funcionalidades

- 🤖 **Validação Automática com IA** - Análise inteligente de screenshots usando YOLOv8
- 📊 **Relatórios Detalhados** - Status PASS/WARNING/FAIL com explicações em linguagem natural
- 👥 **Gerenciamento de Usuários** - Autenticação JWT e roles (user/admin)
- 📈 **Dashboard com Métricas** - Visualização de histórico, ranking e evolução
- 🔄 **Processamento em Lote** - Até 20 imagens por requisição
- 🔐 **Sistema de Convites** - Onboarding controlado com códigos temporários (48h)
- 📱 **Interface Intuitiva** - 10 telas profissionais para admin e usuários

---

## 🎬 Demonstração

### Screenshots das Interfaces

#### Tela de Login
[![Telade-Login.jpg](https://i.postimg.cc/vZdsNNcq/Telade-Login.jpg)](https://postimg.cc/MvtNct0V)

#### Dashboard Administrativo
[![Dashboard-ADM.jpg](https://i.postimg.cc/y6yYcRnk/Dashboard-ADM.jpg)](https://postimg.cc/fkkNhJGN)

#### Validação de Screenshots
[![Valid-Screenshots.jpg](https://i.postimg.cc/Njf4BRCV/Valid-Screenshots.jpg)](https://postimg.cc/tYwPznjt)

#### Minhas Estatísticas
[![Estatisticas.jpg](https://i.postimg.cc/PrfZwTbG/Estatisticas.jpg)](https://postimg.cc/xq7crrFg)

---

## 🛠️ Tecnologias Utilizadas

### Frontend
- ![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)<br/>
- ![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)<br/>
- ![HTML5](https://img.shields.io/badge/HTML5-E34C26?style=for-the-badge&logo=html5&logoColor=white)<br/>
- ![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)

### Backend
- ![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)<br/>
- ![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)<br/>
- ![Uvicorn](https://img.shields.io/badge/Uvicorn-499848?style=for-the-badge&logo=uvicorn&logoColor=white)

### IA e Visão Computacional
- ![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-FF6B6B?style=for-the-badge)<br/>
- ![NumPy](https://img.shields.io/badge/NumPy-013243?style=for-the-badge&logo=numpy&logoColor=white)<br/>
- ![Pillow](https://img.shields.io/badge/Pillow-4B8BBE?style=for-the-badge&logo=python&logoColor=white)

### Infraestrutura
- ![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)<br/>
- ![Nginx](https://img.shields.io/badge/Nginx-009639?style=for-the-badge&logo=nginx&logoColor=white)<br/>
- ![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)

### Segurança
- ![JWT](https://img.shields.io/badge/JWT-000000?style=for-the-badge&logo=json-web-tokens&logoColor=white)<br/>
- ![Bcrypt](https://img.shields.io/badge/Bcrypt-Security-green?style=for-the-badge)

---

## 🚀 Começando

### 📦 Pré-requisitos

Antes de começar, certifique-se de ter instalado:<br/>
- [Python](https://www.python.org/) (versão 3.10 ou superior)<br/>
- [Node.js](https://nodejs.org/) (versão 18 ou superior)<br/>
- [npm](https://www.npmjs.com/) ou [yarn](https://yarnpkg.com/)<br/>
- [Git](https://git-scm.com/)<br/>
- [Docker](https://www.docker.com/) (opcional, para containerização)

### 💻 Instalação

1. **Clone o repositório**
```bash
git clone https://github.com/RickDevAI/VisionIA.git
cd VisionIA
