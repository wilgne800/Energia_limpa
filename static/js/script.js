document.addEventListener('DOMContentLoaded', function() {
    // ==================== Chatbot Functionality ====================
    const chatbotToggle = document.getElementById('chatbot-toggle');
    const chatbotWidget = document.querySelector('.chatbot-widget');
    const closeChat = document.getElementById('close-chat');
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendMessage = document.getElementById('send-message');

    // Toggle chatbot visibility
    chatbotToggle.addEventListener('click', function() {
        chatbotWidget.classList.toggle('active');
        this.classList.toggle('active');

        if (chatbotWidget.classList.contains('active')) {
            userInput.focus();
        }
    });

    closeChat.addEventListener('click', function() {
        chatbotWidget.classList.remove('active');
        chatbotToggle.classList.remove('active');
    });

    // Send message function
    function sendUserMessage() {
        const message = userInput.value.trim();
        if (message === '') return;

        addMessageToChat(message, 'user');
        userInput.value = '';

        fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                addMessageToChat('Desculpe, ocorreu um erro. Tente novamente.', 'bot');
                console.error(data.error);
            } else {
                addMessageToChat(data.response, 'bot');
            }
        })
        .catch(error => {
            addMessageToChat('Erro de conexão. Tente mais tarde.', 'bot');
            console.error('Error:', error);
        });
    }

    function addMessageToChat(message, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add(`${sender}-message`);

        const messageP = document.createElement('p');
        messageP.textContent = message;
        messageDiv.appendChild(messageP);

        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    sendMessage.addEventListener('click', sendUserMessage);

    userInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendUserMessage();
        }
    });

    // ==================== Smooth Scrolling ====================
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();

            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);

            if (targetElement) {
                window.scrollTo({
                    top: targetElement.offsetTop - 80,
                    behavior: 'smooth'
                });

                if (window.innerWidth <= 768) {
                    document.getElementById('mainNav').classList.remove('active');
                }
            }
        });
    });

    // ==================== Economy Calculator ====================
    const form = document.getElementById('economy-calculator');
    const resultDiv = document.getElementById('calculator-result');
    const modal = document.getElementById('savings-modal');
    const closeModal = document.querySelector('.close-modal');

    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();

            const billAmount = parseFloat(document.getElementById('bill-amount').value);
            const consumerType = document.getElementById('consumer-type').value;

            if (!billAmount || !consumerType) {
                Swal.fire('Erro', 'Preencha todos os campos', 'error');
                return;
            }

            fetch('/calculate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    bill_amount: billAmount,
                    consumer_type: consumerType
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) throw new Error(data.error);

                document.getElementById('original-value').textContent = data.original_value;
                document.getElementById('discounted-value').textContent = data.discounted_value;
                document.getElementById('savings-value').textContent = data.monthly_savings;

                resultDiv.style.display = 'block';
                document.getElementById('annual-savings-value').textContent = data.annual_savings;
                document.getElementById('savings-percent').textContent = data.savings_percent;
                modal.style.display = 'block';
            })
            .catch(error => {
                Swal.fire('Erro', error.message, 'error');
            });
        });

        closeModal.addEventListener('click', function() {
            modal.style.display = 'none';
        });

        window.addEventListener('click', function(event) {
            if (event.target === modal) {
                modal.style.display = 'none';
            }
        });
    }

    // ==================== Mobile Menu ====================
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const mainNav = document.getElementById('mainNav');

    if (mobileMenuBtn && mainNav) {
        mobileMenuBtn.addEventListener('click', function() {
            this.classList.toggle('active');
            mainNav.classList.toggle('active');
            document.body.style.overflow = mainNav.classList.contains('active') ? 'hidden' : '';
        });

        document.querySelectorAll('.main-nav a').forEach(link => {
            link.addEventListener('click', function() {
                mobileMenuBtn.classList.remove('active');
                mainNav.classList.remove('active');
                document.body.style.overflow = '';
            });
        });
    }

    // ==================== FAQ Accordion ====================
    const faqItems = document.querySelectorAll('.faq-item');

    faqItems.forEach(item => {
        const question = item.querySelector('.faq-question');

        question.addEventListener('click', () => {
            faqItems.forEach(otherItem => {
                if (otherItem !== item) {
                    otherItem.classList.remove('active');
                }
            });

            item.classList.toggle('active');
        });
    });

    // ==================== Contact Form (ÚNICO listener) ====================
    const contactForm = document.getElementById('contact-form');

    if (contactForm) {
        contactForm.addEventListener('submit', async function(e) {
            e.preventDefault();

            const formData = {
                name: document.getElementById('name').value,
                email: document.getElementById('email').value,
                phone: document.getElementById('phone').value,
                subject: document.getElementById('subject').value,
                message: document.getElementById('message').value
            };

            // Validação
            if (!formData.name || !formData.phone || !formData.subject) {
                Swal.fire('Erro', 'Preencha os campos obrigatórios!', 'error');
                return;
            }

            Swal.fire({
                title: 'Enviando...',
                html: 'Aguarde enquanto processamos seu formulário.',
                allowOutsideClick: false,
                didOpen: () => Swal.showLoading()
            });

            try {
                const response = await fetch('/submit-form', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(formData)
                });

                const data = await response.json();

                if (data.success) {
                    Swal.fire({
                        title: 'Sucesso!',
                        html: `📱 Verifique seu WhatsApp para continuar.<br><br>
                               <small>Selecione "1 - Falar com assistente virtual" para começar.</small>`,
                        icon: 'success',
                        confirmButtonText: 'OK'
                    });
                    this.reset();
                } else {
                    throw new Error(data.error || 'Erro ao enviar formulário');
                }
            } catch (error) {
                Swal.fire('Erro', error.message, 'error');
            }
        });
    }
});