document.addEventListener('DOMContentLoaded', () => {
    // --- STATE MANAGEMENT ---
    let gameFrames = [];
    let currentFrameIndex = 0;
    let isPaused = true;
    let animationSpeed = 100; // ms per frame
    let animationInterval;
    let pollingInterval;

    // --- ELEMENT REFERENCES ---
    // Setup Panel
    const runBtn = document.getElementById('runMatchBtn');
    const editNameBtn = document.getElementById('editNameBtn');
    const teamNameDisplay = document.getElementById('teamNameDisplay');
    const teamNameInput = document.getElementById('teamNameInput');
    
    // Visualizer
    const canvas = document.getElementById('tronCanvas');
    const ctx = canvas.getContext('2d');
    
    // Replay Controls
    const playPauseBtn = document.getElementById('playPauseBtn');
    const restartBtn = document.getElementById('restartBtn');
    const stepBackBtn = document.getElementById('stepBackBtn');
    const stepFwdBtn = document.getElementById('stepFwdBtn');
    const speedSlider = document.getElementById('speedSlider');
    const speedDisplay = document.getElementById('speedDisplay');
    const scrubber = document.getElementById('scrubber');
    
    // Info Panel
    const resultDisplay = document.getElementById('resultDisplay');
    const p1Status = document.getElementById('p1Status');
    const p2Status = document.getElementById('p2Status');
    const p1Length = document.getElementById('p1Length');
    const p2Length = document.getElementById('p2Length');
    const turnDisplay = document.getElementById('turnDisplay');
    
    // --- EVENT LISTENERS ---
    runBtn.addEventListener('click', startMatch);
    editNameBtn.addEventListener('click', toggleNameEdit);
    playPauseBtn.addEventListener('click', togglePlayPause);
    restartBtn.addEventListener('click', restartAnimation);
    stepBackBtn.addEventListener('click', () => step(-1));
    stepFwdBtn.addEventListener('click', () => step(1));
    speedSlider.addEventListener('input', handleSpeedChange);
    scrubber.addEventListener('input', handleScrubberChange);

    // --- CORE LOGIC ---
    async function startMatch() {
        clearInterval(animationInterval);
        clearInterval(pollingInterval);
        // UI TWEAK: Set status text and spinner together in the info panel
        resultDisplay.innerHTML = 'Requesting match... <i class="fas fa-spinner fa-spin"></i>';
        runBtn.disabled = true;

        const payload = {
            language: document.getElementById('language').value,
            bot_path: document.getElementById('botPath').value,
            team_name: teamNameDisplay.textContent
        };

        try {
            const response = await fetch('/run-match', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await response.json();
            
            if (data.status === 'started') {
                // UI TWEAK: Update status text
                resultDisplay.innerHTML = 'Match running... <i class="fas fa-spinner fa-spin"></i>';
                pollForResult(data.match_id);
            } else {
                throw new Error(data.error || 'Failed to start match.');
            }
        } catch (error) {
            resultDisplay.textContent = `Error: ${error.message}`;
            runBtn.disabled = false;
        }
    }

    function pollForResult(matchId) {
        pollingInterval = setInterval(async () => {
            try {
                const response = await fetch(`/match-status/${matchId}`);
                const data = await response.json();

                // if (data.status === 'complete') {
                //     clearInterval(pollingInterval);
                //     resultDisplay.textContent = data.log.result.winner; // Hide spinner by replacing innerHTML
                //     gameFrames = data.log.frames;
                //     runBtn.disabled = false;
                //     setupAnimation();
                //     } 

                if (data.status === 'complete') {
                    clearInterval(pollingInterval);

                    // --- NEW DEBUG LOGGING ---
                    if (data.log && data.log.debug_info) {
                        console.groupCollapsed("--- Match Debug Info ---"); // Start a collapsed group

                        const p1_stderr = data.log.debug_info.p1_stderr;
                        if (p1_stderr && p1_stderr.trim() !== '') {
                            console.error("Player 1 (Your Bot) Crash Log:\n", p1_stderr);
                        }

                        const p2_stderr = data.log.debug_info.p2_stderr;
                        if (p2_stderr && p2_stderr.trim() !== '') {
                            console.error("Player 2 (Opponent) Crash Log:\n", p2_stderr);
                        }

                        // Also log the detailed move-by-move data
                        console.log("Move Details:", data.log.debug_info.move_details);
                        
                        console.groupEnd(); // End the group
                    }
                    // --- END OF NEW LOGGING ---

                    resultDisplay.textContent = data.log.result.winner;
                    gameFrames = data.log.frames;
                    runBtn.disabled = false;
                    setupAnimation();
                }
                
                else if (data.status === 'error') {
                clearInterval(pollingInterval);
                resultDisplay.textContent = `Error: ${data.log.error}`;
                console.error('Raw error output:', data.log.raw_output);
                runBtn.disabled = false;
                }
                // If status is "running", do nothing and wait for the next poll.
            } catch (error) {
                clearInterval(pollingInterval);
                resultDisplay.textContent = `Polling Error: ${error.message}`;
                runBtn.disabled = false;
            }
        }, 2000); // Poll every 2 seconds
    }
    
    // --- ANIMATION & DRAWING ---
    function setupAnimation() {
        currentFrameIndex = 0;
        isPaused = false;
        scrubber.max = gameFrames.length - 1;
        playPauseBtn.innerHTML = '<i class="fas fa-pause"></i>';
        startAnimationInterval();
        updateFrame(); // Draw the first frame immediately
    }

    function startAnimationInterval() {
        clearInterval(animationInterval);
        animationInterval = setInterval(() => {
            if (!isPaused) {
                if (currentFrameIndex < gameFrames.length - 1) {
                    currentFrameIndex++;
                    updateFrame();
                } else {
                    isPaused = true; // Pause at the end
                    playPauseBtn.innerHTML = '<i class="fas fa-play"></i>';
                }
            }
        }, animationSpeed);
    }
    
    function updateFrame() {
        if (!gameFrames || gameFrames.length === 0) return;
        const frame = gameFrames[currentFrameIndex];
        const boardConfig = frame.board;
        const cellWidth = canvas.width / boardConfig.width;
        const cellHeight = canvas.height / boardConfig.height;

        drawFrame(frame, cellWidth, cellHeight);
        updateInfoPanel(frame);
        scrubber.value = currentFrameIndex;
    }

    function drawFrame(frame, cellW, cellH) {
        // BUG FIX: Use direct color values, not CSS variables.
        const bgColor = '#676e78ff';
        const gridColor = 'rgba(117, 68, 68, 0.05)';
        const p1Color = '#000000ff';
        const p2Color = '#ffffffff';
        
        // Clear and draw grid
        ctx.fillStyle = bgColor;
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.strokeStyle = gridColor;
        ctx.lineWidth = 1;
        for (let x = 0; x <= canvas.width; x += cellW) {
            ctx.beginPath();
            ctx.moveTo(x, 0);
            ctx.lineTo(x, canvas.height);
            ctx.stroke();
        }
        for (let y = 0; y <= canvas.height; y += cellH) {
            ctx.beginPath();
            ctx.moveTo(0, y);
            ctx.lineTo(canvas.width, y);
            ctx.stroke();
        }

        // Draw Player 1
        ctx.fillStyle = p1Color;
        frame.p1.body.forEach(part => ctx.fillRect(part.x * cellW, part.y * cellH, cellW, cellH));
        // Draw Player 2
        ctx.fillStyle = p2Color;
        frame.p2.body.forEach(part => ctx.fillRect(part.x * cellW, part.y * cellH, cellW, cellH));
        
        // Draw Heads and Death markers
        drawHead(frame.p1, cellW, cellH);
        drawHead(frame.p2, cellW, cellH);
    }

    function drawHead(player, cellW, cellH) {
        const headX = player.head.x * cellW;
        const headY = player.head.y * cellH;
        
        const p1HeadColor = '#6aff00ff';
        const p2HeadColor = '#00ff2fff';
        const deadColor = '#000000ff';

        const headColor = player.id === 'p1' ? p1HeadColor : p2HeadColor;

        if (player.alive) {
            ctx.fillStyle = headColor;
            ctx.fillRect(headX, headY, cellW, cellH);

            // Draw direction triangle
            ctx.fillStyle = 'white';
            ctx.beginPath();
            const [dx, dy] = player.direction;
            const centerX = headX + cellW / 2;
            const centerY = headY + cellH / 2;
            if (dx === 1) { // Right
                ctx.moveTo(centerX + cellW * 0.3, centerY);
                ctx.lineTo(centerX - cellW * 0.3, centerY - cellH * 0.3);
                ctx.lineTo(centerX - cellW * 0.3, centerY + cellH * 0.3);
            } else if (dx === -1) { // Left
                ctx.moveTo(centerX - cellW * 0.3, centerY);
                ctx.lineTo(centerX + cellW * 0.3, centerY - cellH * 0.3);
                ctx.lineTo(centerX + cellW * 0.3, centerY + cellH * 0.3);
            } else if (dy === 1) { // Down
                ctx.moveTo(centerX, centerY + cellH * 0.3);
                ctx.lineTo(centerX - cellW * 0.3, centerY - cellH * 0.3);
                ctx.lineTo(centerX + cellW * 0.3, centerY - cellH * 0.3);
            } else { // Up (and default)
                ctx.moveTo(centerX, centerY - cellH * 0.3);
                ctx.lineTo(centerX - cellW * 0.3, centerY + cellH * 0.3);
                ctx.lineTo(centerX + cellW * 0.3, centerY + cellH * 0.3);
            }
            ctx.closePath();
            ctx.fill();
        } else {
            // Draw Death 'X'
            ctx.strokeStyle = deadColor;
            ctx.lineWidth = 3;
            ctx.beginPath();
            ctx.moveTo(headX + cellW * 0.2, headY + cellH * 0.2);
            ctx.lineTo(headX + cellW * 0.8, headY + cellH * 0.8);
            ctx.moveTo(headX + cellW * 0.8, headY + cellH * 0.2);
            ctx.lineTo(headX + cellW * 0.2, headY + cellH * 0.8);
            ctx.stroke();
        }
    }
    
    // --- UI HELPERS ---
    function updateInfoPanel(frame) {
        p1Status.textContent = frame.p1.alive ? 'Alive' : 'Dead';
        p2Status.textContent = frame.p2.alive ? 'Alive' : 'Dead';
        p1Length.textContent = frame.p1.body.length;
        p2Length.textContent = frame.p2.body.length;
        turnDisplay.textContent = `${frame.turn} / ${gameFrames.length - 1}`;
    }

    function togglePlayPause() {
        // FEATURE: Auto-restart if at the end
        if (isPaused && currentFrameIndex >= gameFrames.length - 1 && gameFrames.length > 0) {
            restartAnimation();
            return;
        }
        
        isPaused = !isPaused;
        playPauseBtn.innerHTML = isPaused ? '<i class="fas fa-play"></i>' : '<i class="fas fa-pause"></i>';
    }

    function restartAnimation() {
        currentFrameIndex = 0;
        isPaused = false;
        playPauseBtn.innerHTML = '<i class="fas fa-pause"></i>';
        startAnimationInterval();
        updateFrame();
    }

    function step(change) {
        if (!isPaused) togglePlayPause();
        currentFrameIndex = Math.max(0, Math.min(gameFrames.length - 1, currentFrameIndex + change));
        updateFrame();
    }

    // function handleSpeedChange() {
    //     const speedMultiplier = parseFloat(speedSlider.value);
    //     animationSpeed = 100 / speedMultiplier;
    //     speedDisplay.textContent = `${speedMultiplier}x`;
    //     if (!isPaused) startAnimationInterval();
    // }

    function handleSpeedChange() {
    const speedMultiplier = parseFloat(speedSlider.value);
    animationSpeed = 100 / speedMultiplier;
    // Update this line to format the text
    speedDisplay.textContent = `${speedMultiplier.toFixed(2)}x`; 
    if (!isPaused) startAnimationInterval();
}
    
    function handleScrubberChange() {
        if (!isPaused) togglePlayPause();
        currentFrameIndex = parseInt(scrubber.value, 10);
        updateFrame();
    }

    function toggleNameEdit() {
        const isEditing = !teamNameInput.classList.contains('hidden');
        if (isEditing) {
            teamNameDisplay.textContent = teamNameInput.value;
            teamNameInput.classList.add('hidden');
            teamNameDisplay.classList.remove('hidden');
        } else {
            teamNameInput.classList.remove('hidden');
            teamNameDisplay.classList.add('hidden');
            teamNameInput.focus();
        }
    }
    
    teamNameInput.addEventListener('blur', toggleNameEdit);
    teamNameInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') toggleNameEdit();
    });
});