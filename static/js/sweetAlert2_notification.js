
   
        document.addEventListener('DOMContentLoaded', function() {
            let messagesText = '';
            let messageIcon = 'info'; // Icône par défaut

            {% for message in messages %}
                // Concaténer les messages s'il y en a plusieurs
                messagesText += '{{ message|escapejs }}\\n'; 

                // Déterminer l'icône en fonction du tag du message
                {% if message.tags == 'success' %}
                    messageIcon = 'success';
                {% elif message.tags == 'warning' %}
                    messageIcon = 'warning';
                {% elif message.tags == 'error' %}
                    messageIcon = 'error';
                {% endif %}
            {% endfor %}

            if (messagesText) {
                Swal.fire({
                    title: 'Notification',
                    html: messagesText.replace(/\\n/g, '<br>'), // Remplace les sauts de ligne par des <br> pour un meilleur affichage
                    icon: messageIcon,
                    confirmButtonText: 'OK',
                    confirmButtonColor: '#3085d6'
                });
            }
        });
