/**
 * Function to make a popup notification in the GUI
 * @param {*} message Message to be displayed in the popup
 */
export function showNotification(message) {
    var notificationsDiv = document.getElementById('notifications');

    var notification = document.createElement('div');
    notification.className = 'notification';
    notification.textContent = message;
    notificationsDiv.appendChild(notification);
    
    // Show the notification with a slight delay to allow CSS transition
    setTimeout(function() {
        // Scroll to the bottom after adding the notification
        notificationsDiv.scrollTop = notificationsDiv.scrollHeight;

        notification.classList.add('show');
    }, 100);

    // Remove the notification after 5 seconds
    setTimeout(function() {
        notification.classList.remove('show');
        // Remove the element after transition ends
        setTimeout(function() {
            notificationsDiv.removeChild(notification);
        }, 500);
    }, 5000);
}