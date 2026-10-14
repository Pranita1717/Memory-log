// static/script.js

// --- HELPER: Save Score ---
// Accepts an optional 'customMsg' to show detailed feedback (used in Words game)
function saveScore(game, score, customMsg) {
    // 1. Show Feedback
    alert(customMsg || `Game Over! Score: ${score}`);
    
    // 2. Send to Backend
    fetch('/submit_score', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ game: game, score: score })
    }).then(() => {
        window.location.href = '/dashboard';
    });
}

// ==========================================
// GAME 1: MATCHING PAIRS
// ==========================================
let matchTimer;

function initMatching() {
    // 1. Define Images using your local paths
    // NOTE: Ensure your 'src' folder is next to your HTML file or accessible via URL
    const items = [
        { name: 'apple',      img: '/static/src/red-apple.png' },
        { name: 'banana',     img: '/static/src/banana.png' },
        { name: 'grapes',     img: '/static/src/grapes.png' },
        { name: 'watermelon', img: '/static/src/watermelon.png' },
        { name: 'mango',      img: '/static/src/mango.png' },
        { name: 'pineapple',  img: '/static/src/pineapple.png' }
    ];

    const board = document.getElementById('game-board-matching');
    const moveDisplay = document.getElementById('move-count');
    const timeDisplay = document.getElementById('time-count');
    
    // Safety check: Stop if this HTML element doesn't exist (e.g. user is on a different page)
    if (!board) return;

    // 2. Setup Board
    let deck = [...items, ...items]; // Duplicate to create pairs
    deck.sort(() => 0.5 - Math.random()); // Shuffle

    board.innerHTML = '';
    let openCards = [];
    let moves = 0;
    let matches = 0;
    let seconds = 0;

    // 3. Reset Stats
    if(moveDisplay) moveDisplay.innerText = '0';
    if(timeDisplay) timeDisplay.innerText = '0s';
    if (matchTimer) clearInterval(matchTimer);
    
    // Start Timer
    matchTimer = setInterval(() => {
        seconds++;
        if(timeDisplay) timeDisplay.innerText = seconds + 's';
    }, 1000);

    // 4. Create Cards
    deck.forEach(item => {
        const card = document.createElement('div');
        card.className = 'card-tile';
        
        card.innerHTML = `
            <div class="card-inner">
                <div class="card-front">❓</div>
                <div class="card-back">
                    <img src="${item.img}" alt="${item.name}">
                </div>
            </div>
        `;

        card.onclick = () => {
            // Logic: Ignore click if card is already flipped or 2 cards are already open
            if(card.classList.contains('flipped') || openCards.length >= 2) return;
            
            // Flip the card
            card.classList.add('flipped');
            openCards.push({ element: card, name: item.name });
            
            // Check Match
            if(openCards.length === 2) {
                moves++;
                if(moveDisplay) moveDisplay.innerText = moves;

                const card1 = openCards[0];
                const card2 = openCards[1];

                if(card1.name === card2.name) {
                    // MATCH!
                    matches++;
                    openCards = [];
                    // Check Win Condition
                    if(matches === items.length) {
                        clearInterval(matchTimer);
                        setTimeout(() => {
                            // Score Calculation: 100 - (moves * 2) - (seconds / 5)
                            let finalScore = Math.max(0, 100 - (moves * 2) - Math.floor(seconds / 5));
                            saveScore('Matching', finalScore);
                        }, 500);
                    }
                } else {
                    // NO MATCH - Flip back after delay
                    setTimeout(() => {
                        card1.element.classList.remove('flipped');
                        card2.element.classList.remove('flipped');
                        openCards = [];
                    }, 1000);
                }
            }
        };
        board.appendChild(card);
    });
}

// ==========================================
// GAME 2: WORD RECALL (With Time Bar)
// ==========================================
const wordPool = [
    "Apple", "River", "Hotel", "Mouse", "Train", "Bread", "Clock", "Grass", 
    "Music", "Table", "Phone", "Water", "Chair", "Light", "Plant", "Smile",
    "Beach", "Party", "Dream", "Space", "Tiger", "Lemon", "House", "Radio",
    "Shoes", "Cloud", "Paper", "Pencil", "Window", "Garden"
];

function initWords() {
    const container = document.getElementById('word-container');
    const inputArea = document.getElementById('input-area');
    const instruct = document.getElementById('instruction-text');
    const timerContainer = document.getElementById('timer-container');
    const timerBar = document.getElementById('timer-bar');
    
    // Safety check
    if (!container) return;

    // 1. Pick 5 random unique words
    let deck = [...wordPool].sort(() => 0.5 - Math.random());
    window.currentWords = deck.slice(0, 5); 

    // 2. Display Words
    container.innerHTML = '';
    window.currentWords.forEach(word => {
        const div = document.createElement('div');
        div.className = 'word-card';
        div.innerText = word;
        container.appendChild(div);
    });

    // 3. Start Timer Bar Animation
    if (timerContainer && timerBar) {
        timerContainer.style.display = 'block'; // Show bar
        
        // Reset animation
        timerBar.style.transition = 'none';
        timerBar.style.width = '100%';
        
        // Force Reflow (flush CSS changes so browser sees the 100% width)
        void timerBar.offsetWidth; 
        
        // Animate to 0% over 5 seconds
        timerBar.style.transition = 'width 5s linear';
        timerBar.style.width = '0%';
    }

    // 4. Hide after 5 seconds
    setTimeout(() => {
        container.innerHTML = ''; // Clear words
        if (timerContainer) timerContainer.style.display = 'none'; // Hide bar
        
        if (instruct) instruct.innerText = "What were the words?";
        if (inputArea) {
            inputArea.style.display = 'block';
            const input = document.getElementById('user-words');
            if (input) input.focus();
        }
    }, 5000);
}

function checkWords() {
    const inputEl = document.getElementById('user-words');
    if(!inputEl) return;

    const rawInput = inputEl.value;
    // Split by comma or space and remove empty entries
    const userList = rawInput.toLowerCase().split(/[\s,]+/).filter(w => w.length > 0);
    
    let score = 0;
    let correctWords = [];
    let missedWords = [];

    // Check against current target words
    window.currentWords.forEach(target => {
        if (userList.includes(target.toLowerCase())) {
            score++;
            correctWords.push(target);
        } else {
            missedWords.push(target);
        }
    });

    const finalScore = Math.round((score / window.currentWords.length) * 100);
    
    // Detailed Feedback Message
    let msg = `Score: ${finalScore}/100\n\n`;
    msg += `✅ You remembered: ${correctWords.join(", ") || "None"}\n`;
    msg += `❌ You missed: ${missedWords.join(", ")}`;

    saveScore('Word Recall', finalScore, msg);
}

// ==========================================
// GAME 3: PATTERN SEQUENCE
// ==========================================
let sequence = [], userIdx = 0;

function startPattern() {
    sequence = [];
    const btn = document.getElementById('start-btn');
    if(btn) btn.style.display = 'none';
    nextRound();
}

function nextRound() {
    userIdx = 0;
    sequence.push(Math.floor(Math.random() * 4)); // Add random number (0-3) to sequence
    playSequence();
}

function playSequence() {
    let i = 0;
    const msg = document.getElementById('msg');
    if(msg) msg.innerText = "Watch...";
    
    const interval = setInterval(() => {
        if(i >= sequence.length) {
            clearInterval(interval);
            if(msg) msg.innerText = "Your Turn!";
            return;
        }
        flash(sequence[i]);
        i++;
    }, 800);
}

function flash(id) {
    const pad = document.getElementById('pad-'+id);
    if (pad) {
        pad.classList.add('active');
        setTimeout(() => pad.classList.remove('active'), 400);
    }
}

function padClick(id) {
    // Only allow clicks if game has started
    if(sequence.length === 0) return;
    
    flash(id);
    
    // Check if correct pad was clicked
    if(id !== sequence[userIdx]) {
        saveScore('Pattern', sequence.length * 10);
        return;
    }
    
    userIdx++;
    
    // If finished current sequence, go to next round
    if(userIdx === sequence.length) {
        setTimeout(nextRound, 1000);
    }
}