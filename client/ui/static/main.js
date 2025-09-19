document.addEventListener('DOMContentLoaded', () => {
    // --- STATE MANAGEMENT ---
    let gameFrames = [];
    let currentFrameIndex = 0;
    let isPaused = true;
    let animationSpeed = 100; // ms per frame
    let animationInterval;
    let pollingInterval;

    // --- ELEMENT REFERENCES ---

    //submission stuff
    const submitBtn = document.getElementById('submitBtn');
    const submitModal = document.getElementById('submitModal');
    const modalTeamName = document.getElementById('modalTeamName');
    const passwordInput = document.getElementById('passwordInput');
    const cancelSubmitBtn = document.getElementById('cancelSubmitBtn');
    const confirmSubmitBtn = document.getElementById('confirmSubmitBtn');
    const submitStatus = document.getElementById('submitStatus');

    // Setup Panel
    const runBtn = document.getElementById('runMatchBtn');
    const editNameBtn = document.getElementById('editNameBtn');
    const teamNameDisplay = document.getElementById('teamNameDisplay');
    const teamNameInput = document.getElementById('teamNameInput');
    const tabs = document.querySelectorAll('.tab-btn');
    const tabPanels = document.querySelectorAll('.tab-panel');
    const logOutput = document.getElementById('logOutput');

    // const botPathDisplay = document.getElementById('botPathDisplay');
    // const browseBtn = document.getElementById('browseBtn');

    // Player 1
    const botPathDisplayP1 = document.getElementById('botPathDisplayP1');
    // Player 2
    const opponentType = document.getElementById('opponentType');
    const p2FileSelector = document.getElementById('p2FileSelector');
    const botPathDisplayP2 = document.getElementById('botPathDisplayP2');

    // Get both browse buttons
    const browseBtns = document.querySelectorAll('.browseBtn');
    
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
    // browseBtn.addEventListener('click', selectBotFile);
    opponentType.addEventListener('change', handleOpponentTypeChange);
    browseBtns.forEach(btn => btn.addEventListener('click', selectBotFile));
    submitBtn.addEventListener('click', handleSubmit);
    cancelSubmitBtn.addEventListener('click', () => submitModal.classList.add('hidden'));
    confirmSubmitBtn.addEventListener('click', uploadBot);

    // --- CORE LOGIC ---

    function handleOpponentTypeChange() 
    {
        if (opponentType.value === 'human') {
            p2FileSelector.classList.remove('hidden');
        } else {
            p2FileSelector.classList.add('hidden');
        }
    }

    // Call it once at the start to set the initial state
    handleOpponentTypeChange();
    
    async function selectBotFile() 
    {
        const player = event.target.dataset.player; // Gets "P1" or "P2" from the button
        const path = await window.pywebview.api.select_file();
        if (path) {
            if (player === 'P1') {
                botPathDisplayP1.textContent = path;
            } else {
                botPathDisplayP2.textContent = path;
            }
        }
    }

    async function selectBotFolder() 
    {
        // This 'pywebview.api.select_folder' calls the Python function we exposed.
        const path = await window.pywebview.api.select_folder();
        if (path) {
            botPathDisplay.textContent = path;
        }
    }

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            const targetPanelId = tab.dataset.tab;
            tabPanels.forEach(panel => {
                if (panel.id === targetPanelId) {
                    panel.classList.remove('hidden');
                } else {
                    panel.classList.add('hidden');
                }
            });
        });
    });

    async function startMatch() {
        clearInterval(animationInterval);
        clearInterval(pollingInterval);
        // UI TWEAK: Set status text and spinner together in the info panel
        resultDisplay.innerHTML = 'Requesting match... <i class="fas fa-spinner fa-spin"></i>';
        runBtn.disabled = true;

        // const payload = {
        //     // language: document.getElementById('language').value,
        //     bot_path: botPathDisplay.textContent, // Read from the display span now
        //     team_name: teamNameDisplay.textContent
        //     };
        const opponent_selection = opponentType.value; // This will be "cpu_easy" or "human"
        const p1_path = botPathDisplayP1.textContent;
        const p2_path = (opponent_selection === 'human') ? botPathDisplayP2.textContent : null;

        const payload = {
            team_name: teamNameDisplay.textContent,
            p1_path: p1_path,
            p2_path: p2_path,
            opponent_selection: opponent_selection // We send the key, e.g., "cpu_easy"
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

            if (data.status === 'complete') {
                clearInterval(pollingInterval);
                const log = data.log;

                // Display the final winner in the info panel
                resultDisplay.textContent = log.result.winner;

                // Build the new interactive log
                buildInteractiveLog(log);

                gameFrames = log.frames;
                runBtn.disabled = false;
                setupAnimation();

            } else if (data.status === 'error') {
                clearInterval(pollingInterval);
                resultDisplay.textContent = `Error: ${data.log.error}`;
                logContainer.textContent = `Server Error: ${data.log.error}\n\nRaw Output:\n${data.log.raw_output}`;
                runBtn.disabled = false;
            }
        } catch (error) {
            clearInterval(pollingInterval);
            resultDisplay.textContent = `Polling Error: ${error.message}`;
            runBtn.disabled = false;
        }
        }, 2000);
    }

    function buildInteractiveLog(log) {
    const logContainer = document.getElementById('logContainer');
    logContainer.innerHTML = ''; // Clear previous log

    if (!log.debug_info) {
        logContainer.textContent = 'No debug info available.';
        return;
    }

    // --- Helper function to create a collapsible section ---
    function createCollapsibleSection(summaryText, contentObject, isOpen = false) {
        const details = document.createElement('details');
        details.open = isOpen;
        const summary = document.createElement('summary');
        summary.textContent = summaryText;

        const content = document.createElement('div');
        content.className = 'log-content';
        const pre = document.createElement('pre');
        pre.textContent = JSON.stringify(contentObject, null, 2);

        content.appendChild(pre);
        details.appendChild(summary);
        details.appendChild(content);
        return details;
    }

    const debugInfo = log.debug_info;

    // Create a collapsible section for crash logs
    if (debugInfo.p1_stderr || debugInfo.p2_stderr) {
        const crashDetails = createCollapsibleSection("Crash Logs", {
            p1_stderr: debugInfo.p1_stderr,
            p2_stderr: debugInfo.p2_stderr,
        }, true); // Open by default if errors exist
        logContainer.appendChild(crashDetails);
    }

    // Create a collapsible section for move details
    if (debugInfo.move_details) {
        const movesDetails = document.createElement('details');
        movesDetails.open = true; // Main "Move Details" is open by default
        movesDetails.innerHTML = `<summary>Move Details</summary>`;
        const movesContent = document.createElement('div');
        movesContent.className = 'log-content';

        for (const turn of debugInfo.move_details) {
            // Each turn is its own collapsible section
            const turnDetails = document.createElement('details');
            turnDetails.innerHTML = `<summary>Turn ${turn.turn}</summary>`;
            const turnContent = document.createElement('div');
            turnContent.className = 'log-content';

            // Add nested collapsible sections for board state and responses
            turnContent.appendChild(createCollapsibleSection('Board State', turn.board_state));
            turnContent.appendChild(createCollapsibleSection('P1 Response', turn.responses.p1));
            turnContent.appendChild(createCollapsibleSection('P2 Response', turn.responses.p2));

            turnDetails.appendChild(turnContent);
            movesContent.appendChild(turnDetails);
        }
        movesDetails.appendChild(movesContent);
        logContainer.appendChild(movesDetails);
    }
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
        const bgColor = '#000000ff';
        const gridColor = 'rgba(118, 37, 218, 1)';
        const p1Color = '#00fff2ff';
        const p2Color = '#fffb00ff';
        
        // Clear and draw grid
        ctx.fillStyle = bgColor;
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.strokeStyle = gridColor;
        ctx.lineWidth = 0.3;
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

        const padding = ctx.lineWidth; // Use the grid line width as padding

        // Draw Player 1
        ctx.fillStyle = p1Color;
        frame.p1.body.forEach(part => {
            ctx.fillRect(
                part.x * cellW + padding,  // Start slightly to the right
                part.y * cellH + padding,  // Start slightly lower
                cellW - padding * 2,       // Make it narrower
                cellH - padding * 2        // Make it shorter
            );
        });
        
        // Draw Player 2
        ctx.fillStyle = p2Color;
        frame.p2.body.forEach(part => {
            ctx.fillRect(
                part.x * cellW + padding,
                part.y * cellH + padding,
                cellW - padding * 2,
                cellH - padding * 2
            );
        });
        
        // Draw Heads and Death markers
        drawHead(frame.p1, cellW, cellH);
        drawHead(frame.p2, cellW, cellH);
    }

    function drawHead(player, cellW, cellH) {
        const headX = player.head.x * cellW;
        const headY = player.head.y * cellH;
        
        const p1HeadColor = '#9500ffff';
        const p2HeadColor = '#ff5100ff';
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
    if (isPaused && currentFrameIndex >= gameFrames.length - 1 && gameFrames.length > 0) {
        restartAnimation();
        return;
    }

    isPaused = !isPaused;

    // Add this line:
    // When unpausing, re-calculate the speed from the slider's current value.
    if (!isPaused) {
        handleSpeedChange(); 
    }

    playPauseBtn.innerHTML = isPaused ? '<i class="fas fa-play"></i>' : '<i class="fas fa-pause"></i>';
    }

    function restartAnimation() {
        currentFrameIndex = 0;
        isPaused = false;
        playPauseBtn.innerHTML = '<i class="fas fa-pause"></i>';
        handleSpeedChange();
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

    function handleSubmit() {
        // Show the modal and populate the team name
        const teamName = teamNameDisplay.textContent;
        const p1_path = botPathDisplayP1.textContent;
        if (!teamName || !p1_path || p1_path.includes("No file selected")) {
            alert("Please enter a team name and select a Player 1 bot file before submitting.");
            return;
        }
        modalTeamName.textContent = teamName;
        passwordInput.value = "";
        submitStatus.textContent = "";
        submitModal.classList.remove('hidden');
    }

    async function uploadBot() 
    {
        submitStatus.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Zipping and uploading...';

        const p1_path = botPathDisplayP1.textContent;

        // 1. Ask Python to create the zip file
        const zipResult = await window.pywebview.api.create_bot_zip(p1_path);

        if (zipResult.error) {
            submitStatus.textContent = `Error: ${zipResult.error}`;
            return;
        }

        // 2. Prepare payload for our own backend
        const payload = {
            team_name: teamNameDisplay.textContent,
            password: passwordInput.value,
            zip_data: zipResult.zip_data // The base64-encoded zip file
        };

        // 3. Send to our backend, which will forward it to the main server
        try {
            const response = await fetch('/submit-to-server', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.error || 'Submission failed.');
            }
            submitStatus.textContent = data.message;
            setTimeout(() => submitModal.classList.add('hidden'), 2000); // Close modal on success
        } catch (error) {
            submitStatus.textContent = `Error: ${error.message}`;
        }
    }   
    
    teamNameInput.addEventListener('blur', toggleNameEdit);
    teamNameInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') toggleNameEdit();
    });
});