// main.js

document.addEventListener('alpine:init', () => {
    Alpine.data('nostalgiaApp', () => ({
        cursorPosition: { x: 0, y: 0 },
        visitorCount: 0,
        title: '🕰️ Nostalgia Site 🕰️',
        displayedTitle: '',
        titleIndex: 0,

        init() {
            this.simulateVisitorCount();
            this.typeTitle();
            this.addNewBadgesToLinks();
        },

        updateCursorPosition(event) {
            this.cursorPosition.x = event.clientX;
            this.cursorPosition.y = event.clientY;
        },

        simulateVisitorCount() {
            this.visitorCount = Math.floor(Math.random() * 10000) + 1;
        },

        typeTitle() {
            if (this.titleIndex < this.title.length) {
                this.displayedTitle += this.title.charAt(this.titleIndex);
                this.titleIndex++;
                setTimeout(() => this.typeTitle(), 100);
            }
        },

        addNewBadgesToLinks() {
            document.querySelectorAll('a').forEach(link => {
                if (Math.random() > 0.8) {
                    const newSpan = document.createElement('span');
                    newSpan.textContent = ' NEW!';
                    newSpan.classList.add('blink');
                    link.appendChild(newSpan);
                }
            });
        },

        playHoverSound() {
            const hoverSound = new Audio('/static/sounds/hover.mp3');
            hoverSound.play();
        }
    }));
});