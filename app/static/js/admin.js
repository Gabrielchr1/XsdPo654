document.addEventListener("DOMContentLoaded", function() {
    // --- 1. LÓGICA PARA O MENU ACORDEÃO ---
    const sidebarItems = document.querySelectorAll(".sidebar-item.has-arrow");

    sidebarItems.forEach(item => {
        const link = item.querySelector('.sidebar-link');
        link.addEventListener("click", function(e) {
            e.preventDefault();

            // Fecha outros submenus abertos
            sidebarItems.forEach(otherItem => {
                if (otherItem !== item) {
                    otherItem.classList.remove('active');
                }
            });

            // Abre ou fecha o submenu atual
            item.classList.toggle('active');
        });
    });

    // --- 2. LÓGICA PARA RECOLHER/EXPANDIR O MENU PRINCIPAL ---
    const sidebarToggle = document.getElementById("sidebarToggle");
    if (sidebarToggle) {
        sidebarToggle.addEventListener("click", function() {
            document.body.classList.toggle("sidebar-collapsed");
        });
    }



    // --- NOVA FUNCIONALIDADE DE CADASTRO DE CLIENTE ---
    const clientTypeToggle = document.getElementById('clientTypeToggle');
    if (clientTypeToggle) {
        const pfTab = document.getElementById('pf-tab');
        const pjTab = document.getElementById('pj-tab');
        const pfForm = document.getElementById('form-pf');
        const pjForm = document.getElementById('form-pj');
        const clientTypeInput = document.getElementById('client_type_input');
        const namePfInput = document.getElementById('name_pf');
        const cpfInput = document.getElementById('cpf');
        const cnpjInput = document.getElementById('cnpj');
        const razaoSocialInput = document.getElementById('razao_social');

        pfTab.addEventListener('click', () => {
            pfForm.classList.remove('d-none');
            pjForm.classList.add('d-none');
            clientTypeInput.value = 'PF';
            // Alterna quais campos são obrigatórios para o formulário
            namePfInput.name = "name";
            cpfInput.name = "cpf_cnpj";
            razaoSocialInput.name = "";
            cnpjInput.name = "";
        });

        pjTab.addEventListener('click', () => {
            pjForm.classList.remove('d-none');
            pfForm.classList.add('d-none');
            clientTypeInput.value = 'PJ';
            // Alterna quais campos são obrigatórios para o formulário
            razaoSocialInput.name = "name";
            cnpjInput.name = "cpf_cnpj";
            namePfInput.name = "";
            cpfInput.name = "";
        });

        // --- PREENCHIMENTO AUTOMÁTICO POR CEP ---
        const cepInput = document.getElementById('cep');
        cepInput.addEventListener('blur', function() {
            const cep = this.value.replace(/\D/g, '');
            if (cep.length === 8) {
                fetch(`https://brasilapi.com.br/api/cep/v1/${cep}`)
                    .then(response => response.json())
                    .then(data => {
                        if (!data.errors) {
                            document.getElementById('logradouro').value = data.street;
                            document.getElementById('bairro').value = data.neighborhood;
                            document.getElementById('cidade').value = data.city;
                            document.getElementById('uf').value = data.state;
                        }
                    })
                    .catch(error => console.error('Erro ao buscar CEP:', error));
            }
        });

        // --- PREENCHIMENTO AUTOMÁTICO POR CNPJ ---
        cnpjInput.addEventListener('blur', function() {
            const cnpj = this.value.replace(/\D/g, '');
            if (cnpj.length === 14) {
                fetch(`https://brasilapi.com.br/api/cnpj/v1/${cnpj}`)
                    .then(response => response.json())
                    .then(data => {
                        if (!data.errors) {
                            document.getElementById('razao_social').value = data.razao_social;
                            document.getElementById('cep').value = data.cep;
                            // Dispara o evento de 'blur' no CEP para preencher o resto do endereço
                            cepInput.dispatchEvent(new Event('blur'));
                        }
                    })
                    .catch(error => console.error('Erro ao buscar CNPJ:', error));
            }
        });
    }



    // --- NOVA FUNCIONALIDADE DE PROPOSTA ---
    const proposalForm = document.querySelector('form'); // Encontra o formulário na página
    if (proposalForm) {
        // Lógica para alternar campos de consumo
        const consumptionRadios = document.querySelectorAll('input[name="consumption_input_type"]');
        const kwhGroup = document.getElementById('kwh-input-group');
        const brlGroup = document.getElementById('brl-input-group');

        consumptionRadios.forEach(radio => {
            radio.addEventListener('change', function() {
                if (this.value === 'kwh') {
                    kwhGroup.classList.remove('d-none');
                    brlGroup.classList.add('d-none');
                } else {
                    brlGroup.classList.remove('d-none');
                    kwhGroup.classList.add('d-none');
                }
            });
        });

        // Lógica para buscar irradiação
        const fetchBtn = document.getElementById('fetchIrradianceBtn');
        const irradianceInput = document.getElementById('solar_irradiance');
        
        fetchBtn.addEventListener('click', function() {
            const clientId = this.dataset.clientId;
            const spinner = this.querySelector('.spinner-border');
            const icon = this.querySelector('.fa-search-location');

            // Mostra o feedback de carregamento
            spinner.classList.remove('d-none');
            icon.classList.add('d-none');
            this.disabled = true;

            fetch(`/admin/get_irradiance/${clientId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        irradianceInput.value = data.irradiance;
                    } else {
                        alert('Erro: ' + data.error);
                    }
                })
                .catch(error => {
                    console.error('Erro na requisição:', error);
                    alert('Ocorreu um erro de rede. Verifique o console para mais detalhes.');
                })
                .finally(() => {
                    // Restaura o botão ao estado normal
                    spinner.classList.add('d-none');
                    icon.classList.remove('d-none');
                    this.disabled = false;
                });
        });
    }


    // --- NOVA FUNCIONALIDADE DE ADICIONAR CONCESSIONARIA (CORRIGIDO) ---
    const modalElement = document.getElementById('addConcessionariaModal');
    if (modalElement) {
        const modal = new bootstrap.Modal(modalElement);
        const form = document.getElementById('addConcessionariaForm');
        
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(form);
            const formAction = form.getAttribute('action'); // Pega a URL correta do atributo action do form

            fetch(formAction, { // Usa a URL correta
                method: 'POST',
                body: formData,
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const select = document.getElementById('concessionaria_select');
                    const newOption = new Option(data.name, data.id, true, true);
                    select.appendChild(newOption);
                    
                    modal.hide();
                    form.reset();
                } else {
                    alert('Erro ao salvar: ' + JSON.stringify(data.errors));
                }
            })
            .catch(error => console.error('Erro:', error));
        });
    }



});