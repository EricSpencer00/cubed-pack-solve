/**
 * T-Tetracube 6×6×6 Cube Packing Viewer
 * 
 * Three.js-based 3D visualization of cube packing solutions.
 * Loads solutions from JSON and renders each piece as a colored voxel group.
 */

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

// =============================================================================
// GLOBAL STATE
// =============================================================================

let scene, camera, renderer, controls;
let solutionData = null;
let currentSolutionIndex = 0;
let pieceGroups = [];
let isExploded = false;
let isWireframe = false;
let currentOpacity = 1.0;
let isServerOnline = false;

// Tutorial state
let tutorialData = null;
let tutorialStep = 0;
let isTutorialMode = false;
let autoPlayInterval = null;

// Patterns state
let patternsData = null;
let currentMode = 'view'; // 'view', 'tutorial', 'patterns'

// Cube parameters
const CUBE_SIZE = 6;
const CELL_SIZE = 1;
const GAP = 0.02; // Small gap between cells

// Color palette for pieces (distinct, visually pleasing)
const COLORS = [
    0xe6194B, 0x3cb44b, 0xffe119, 0x4363d8, 0xf58231,
    0x911eb4, 0x42d4f4, 0xf032e6, 0xbfef45, 0xfabed4,
    0x469990, 0xdcbeff, 0x9A6324, 0xfffac8, 0x800000,
    0xaaffc3, 0x808000, 0xffd8b1, 0x000075, 0xa9a9a9,
    0xe6beff, 0x1f77b4, 0xff7f0e, 0x2ca02c, 0xd62728,
    0x9467bd, 0x8c564b, 0xe377c2, 0x7f7f7f, 0xbcbd22,
    0x17becf, 0xaec7e8, 0xffbb78, 0x98df8a, 0xff9896,
    0xc5b0d5, 0xc49c94, 0xf7b6d2, 0xc7c7c7, 0xdbdb8d,
    0x9edae5, 0x393b79, 0x5254a3, 0x6b6ecf, 0x9c9ede,
    0x637939, 0x8ca252, 0xb5cf6b, 0xcedb9c, 0x8c6d31,
    0xbd9e39, 0xe7ba52, 0xe7cb94, 0x843c39
];

// =============================================================================
// INITIALIZATION
// =============================================================================

function init() {
    // Scene
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x1a1a2e);
    
    // Camera
    camera = new THREE.PerspectiveCamera(
        60,
        window.innerWidth / window.innerHeight,
        0.1,
        1000
    );
    camera.position.set(12, 12, 12);
    camera.lookAt(0, 0, 0);
    
    // Renderer
    renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.shadowMap.enabled = true;
    document.getElementById('canvas-container').appendChild(renderer.domElement);
    
    // Controls
    controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.enableZoom = false;  // Disable zoom
    controls.enablePan = false;   // Disable pan
    controls.target.set(CUBE_SIZE / 2 - 0.5, CUBE_SIZE / 2 - 0.5, CUBE_SIZE / 2 - 0.5);
    controls.update();
    
    // Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.4);
    scene.add(ambientLight);
    
    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(10, 20, 10);
    directionalLight.castShadow = true;
    scene.add(directionalLight);
    
    const directionalLight2 = new THREE.DirectionalLight(0xffffff, 0.3);
    directionalLight2.position.set(-10, -5, -10);
    scene.add(directionalLight2);
    
    // Add cube outline
    addCubeOutline();
    
    // Add coordinate axes helper (small, at corner)
    const axesHelper = new THREE.AxesHelper(1);
    axesHelper.position.set(-1, -1, -1);
    scene.add(axesHelper);
    
    // Event listeners
    window.addEventListener('resize', onWindowResize);
    setupUIListeners();
    
    // Check if local server is available
    checkServerStatus();
    
    // Try to load default solutions file
    tryLoadDefaultSolutions();
    
    // Start animation loop
    animate();
}

function addCubeOutline() {
    const geometry = new THREE.BoxGeometry(CUBE_SIZE, CUBE_SIZE, CUBE_SIZE);
    const edges = new THREE.EdgesGeometry(geometry);
    const material = new THREE.LineBasicMaterial({ 
        color: 0x4a90d9, 
        linewidth: 2,
        transparent: true,
        opacity: 0.5
    });
    const outline = new THREE.LineSegments(edges, material);
    outline.position.set(
        CUBE_SIZE / 2 - 0.5,
        CUBE_SIZE / 2 - 0.5,
        CUBE_SIZE / 2 - 0.5
    );
    scene.add(outline);
}

// =============================================================================
// SOLUTION RENDERING
// =============================================================================

function clearSolution() {
    for (const group of pieceGroups) {
        scene.remove(group);
        group.traverse((child) => {
            if (child.geometry) child.geometry.dispose();
            if (child.material) {
                if (Array.isArray(child.material)) {
                    child.material.forEach(m => m.dispose());
                } else {
                    child.material.dispose();
                }
            }
        });
    }
    pieceGroups = [];
}

function renderSolution(solutionIndex) {
    clearSolution();
    
    if (!solutionData || !solutionData.solutions || solutionIndex >= solutionData.solutions.length) {
        return;
    }
    
    const solution = solutionData.solutions[solutionIndex];
    const pieces = solution.pieces;
    
    pieces.forEach((piece, pieceIndex) => {
        const color = COLORS[pieceIndex % COLORS.length];
        const group = createPiece(piece, color, pieceIndex);
        pieceGroups.push(group);
        scene.add(group);
    });
    
    if (isExploded) {
        applyExplosion();
    }
    
    updateOpacity();
}

function createPiece(cells, color, pieceIndex) {
    const group = new THREE.Group();
    group.userData.pieceIndex = pieceIndex;
    group.userData.originalPositions = [];
    
    // Calculate piece center
    let centerX = 0, centerY = 0, centerZ = 0;
    for (const cell of cells) {
        centerX += cell[0];
        centerY += cell[1];
        centerZ += cell[2];
    }
    centerX /= cells.length;
    centerY /= cells.length;
    centerZ /= cells.length;
    group.userData.center = new THREE.Vector3(centerX, centerY, centerZ);
    
    for (const cell of cells) {
        const [x, y, z] = cell;
        
        // Create voxel (slightly smaller to show gaps)
        const size = CELL_SIZE - GAP;
        const geometry = new THREE.BoxGeometry(size, size, size);
        
        const material = new THREE.MeshPhongMaterial({
            color: color,
            transparent: true,
            opacity: currentOpacity,
            wireframe: isWireframe,
            flatShading: false
        });
        
        const mesh = new THREE.Mesh(geometry, material);
        mesh.position.set(x, y, z);
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        
        // Store original position
        group.userData.originalPositions.push(mesh.position.clone());
        
        // Add edges for better definition
        const edgesGeometry = new THREE.EdgesGeometry(geometry);
        const edgesMaterial = new THREE.LineBasicMaterial({ 
            color: 0x000000,
            transparent: true,
            opacity: 0.3
        });
        const edges = new THREE.LineSegments(edgesGeometry, edgesMaterial);
        mesh.add(edges);
        
        group.add(mesh);
    }
    
    return group;
}

function applyExplosion() {
    const cubeCenter = new THREE.Vector3(
        CUBE_SIZE / 2 - 0.5,
        CUBE_SIZE / 2 - 0.5,
        CUBE_SIZE / 2 - 0.5
    );
    
    for (const group of pieceGroups) {
        const pieceCenter = group.userData.center;
        const direction = new THREE.Vector3().subVectors(pieceCenter, cubeCenter).normalize();
        const offset = direction.multiplyScalar(3); // Explosion distance
        
        group.position.copy(offset);
    }
}

function removeExplosion() {
    for (const group of pieceGroups) {
        group.position.set(0, 0, 0);
    }
}

function updateOpacity() {
    for (const group of pieceGroups) {
        group.traverse((child) => {
            if (child.material && !child.isLineSegments) {
                child.material.opacity = currentOpacity;
            }
        });
    }
}

function toggleWireframe() {
    isWireframe = !isWireframe;
    for (const group of pieceGroups) {
        group.traverse((child) => {
            if (child.material && child.isMesh) {
                child.material.wireframe = isWireframe;
            }
        });
    }
}

// =============================================================================
// DATA LOADING
// =============================================================================

async function tryLoadDefaultSolutions() {
    try {
        const response = await fetch('solutions.json');
        if (response.ok) {
            const data = await response.json();
            loadSolutionData(data);
        }
    } catch (e) {
        console.log('No default solutions.json found. Please load a file.');
        updateUI();
    }
}

function loadSolutionData(data) {
    solutionData = data;
    currentSolutionIndex = 0;
    
    updateUI();
    renderSolution(0);
}

function loadFile(file) {
    const loading = document.getElementById('loading');
    loading.style.display = 'block';
    
    const reader = new FileReader();
    reader.onload = (e) => {
        try {
            const data = JSON.parse(e.target.result);
            loadSolutionData(data);
        } catch (err) {
            alert('Error parsing JSON file: ' + err.message);
        }
        loading.style.display = 'none';
    };
    reader.readAsText(file);
}

// =============================================================================
// LIVE SERVER API
// =============================================================================

async function checkServerStatus() {
    const statusEl = document.getElementById('server-status');
    const generateGroup = document.getElementById('generate-group');
    
    try {
        const response = await fetch('/api/status');
        if (response.ok) {
            const data = await response.json();
            isServerOnline = true;
            statusEl.textContent = 'Live';
            statusEl.className = 'online';
            generateGroup.style.display = 'block';
            
            // If server has solutions, load from API
            if (data.total_solutions > 0) {
                loadFromServer();
            }
        }
    } catch (e) {
        isServerOnline = false;
        statusEl.textContent = 'Static';
        statusEl.className = 'offline';
        generateGroup.style.display = 'none';
    }
}

async function loadFromServer() {
    try {
        const response = await fetch('/api/solutions');
        if (response.ok) {
            const data = await response.json();
            loadSolutionData(data);
        }
    } catch (e) {
        console.error('Failed to load from server:', e);
    }
}

async function generateMore(count) {
    if (!isServerOnline) return;
    
    const generateBtn = document.getElementById('generate-btn');
    const generate50Btn = document.getElementById('generate-50-btn');
    generateBtn.disabled = true;
    generate50Btn.disabled = true;
    generateBtn.textContent = 'Generating...';
    
    try {
        const response = await fetch(`/api/generate?count=${count}`);
        if (response.ok) {
            const data = await response.json();
            
            // Add new solutions to existing data
            if (data.solutions && data.solutions.length > 0) {
                if (!solutionData) {
                    solutionData = { solutions: [], metadata: {} };
                }
                
                // Update IDs and append
                const startId = solutionData.solutions.length;
                for (const sol of data.solutions) {
                    sol.id = startId + solutionData.solutions.length;
                    solutionData.solutions.push(sol);
                }
                
                updateUI();
                
                // If this was the first solutions, render
                if (startId === 0) {
                    renderSolution(0);
                }
            }
            
            console.log(`Generated ${data.generated} solutions, total: ${data.total}`);
        }
    } catch (e) {
        console.error('Failed to generate:', e);
    } finally {
        generateBtn.disabled = false;
        generate50Btn.disabled = false;
        generateBtn.textContent = 'Generate 10 More';
    }
}

// =============================================================================
// UI
// =============================================================================

function updateUI() {
    const solutionCount = document.getElementById('solution-count');
    const solutionCounter = document.getElementById('solution-counter');
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    
    if (solutionData && solutionData.solutions) {
        const total = solutionData.solutions.length;
        solutionCount.textContent = `${total} unique solutions`;
        solutionCounter.textContent = `${currentSolutionIndex + 1} / ${total}`;
        prevBtn.disabled = currentSolutionIndex <= 0;
        nextBtn.disabled = currentSolutionIndex >= total - 1;
    } else {
        solutionCount.textContent = 'No solutions loaded';
        solutionCounter.textContent = '0 / 0';
        prevBtn.disabled = true;
        nextBtn.disabled = true;
    }
}

function setupUIListeners() {
    // File input
    document.getElementById('file-input').addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            loadFile(e.target.files[0]);
        }
    });
    
    // Generate buttons (live server only)
    document.getElementById('generate-btn').addEventListener('click', () => {
        generateMore(10);
    });
    
    document.getElementById('generate-50-btn').addEventListener('click', () => {
        generateMore(50);
    });
    
    // Navigation
    document.getElementById('prev-btn').addEventListener('click', () => {
        if (currentSolutionIndex > 0) {
            currentSolutionIndex--;
            renderSolution(currentSolutionIndex);
            updateUI();
        }
    });
    
    document.getElementById('next-btn').addEventListener('click', () => {
        if (solutionData && currentSolutionIndex < solutionData.solutions.length - 1) {
            currentSolutionIndex++;
            renderSolution(currentSolutionIndex);
            updateUI();
        }
    });
    
    // Keyboard navigation
    document.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
            document.getElementById('prev-btn').click();
        } else if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
            document.getElementById('next-btn').click();
        }
    });
    
    // View options
    document.getElementById('explode-btn').addEventListener('click', () => {
        isExploded = !isExploded;
        if (isExploded) {
            applyExplosion();
        } else {
            removeExplosion();
        }
    });
    
    document.getElementById('wireframe-btn').addEventListener('click', toggleWireframe);
    
    document.getElementById('reset-btn').addEventListener('click', () => {
        camera.position.set(12, 12, 12);
        controls.target.set(CUBE_SIZE / 2 - 0.5, CUBE_SIZE / 2 - 0.5, CUBE_SIZE / 2 - 0.5);
        controls.update();
    });
    
    // Opacity slider
    document.getElementById('opacity-slider').addEventListener('input', (e) => {
        currentOpacity = parseFloat(e.target.value);
        document.getElementById('opacity-value').textContent = Math.round(currentOpacity * 100) + '%';
        updateOpacity();
    });
}

// =============================================================================
// ANIMATION
// =============================================================================

function onWindowResize() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
}

function animate() {
    requestAnimationFrame(animate);
    controls.update();
    renderer.render(scene, camera);
}

// =============================================================================
// MODE SWITCHING
// =============================================================================

function setMode(mode) {
    currentMode = mode;
    
    // Update tab visuals
    document.querySelectorAll('.mode-tab').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.mode === mode);
    });
    
    // Show/hide panels
    document.getElementById('tutorial-panel').classList.toggle('visible', mode === 'tutorial');
    document.getElementById('patterns-panel').classList.toggle('visible', mode === 'patterns');
    
    // Stop auto-play if leaving tutorial mode
    if (mode !== 'tutorial' && autoPlayInterval) {
        stopAutoPlay();
    }
    
    // Load data if needed
    if (mode === 'tutorial' && isServerOnline) {
        loadTutorial();
    } else if (mode === 'patterns' && isServerOnline) {
        loadPatterns();
    }
    
    // Reset view for patterns
    if (mode === 'patterns') {
        clearSolution();
    } else if (mode === 'view' && solutionData) {
        renderSolution(currentSolutionIndex);
    }
}

// =============================================================================
// TUTORIAL MODE
// =============================================================================

async function loadTutorial() {
    if (!isServerOnline || !solutionData || solutionData.solutions.length === 0) {
        document.getElementById('tutorial-tip').textContent = 'Generate at least one solution first!';
        return;
    }
    
    try {
        const response = await fetch(`/api/tutorial/${currentSolutionIndex}`);
        if (response.ok) {
            tutorialData = await response.json();
            tutorialStep = 0;
            updateTutorialUI();
        }
    } catch (e) {
        console.error('Failed to load tutorial:', e);
    }
}

function updateTutorialUI() {
    if (!tutorialData) return;
    
    const step = tutorialData.steps[tutorialStep];
    const total = tutorialData.total_pieces;
    
    document.getElementById('tutorial-step-num').textContent = tutorialStep + 1;
    document.getElementById('tutorial-total').textContent = total;
    document.getElementById('tutorial-progress').textContent = Math.round((tutorialStep + 1) / total * 100) + '%';
    
    // Piece info
    const pieceInfo = document.getElementById('tutorial-piece-info');
    if (step) {
        const grounded = step.is_grounded ? '✓ On ground' : '↑ Elevated';
        const adjacent = step.adjacent_to.length > 0 ? `Connects to: ${step.adjacent_to.join(', ')}` : 'First piece!';
        pieceInfo.innerHTML = `<div style="margin-top:8px;font-size:13px;">${grounded} | ${adjacent}</div>`;
    }
    
    // Tip
    document.getElementById('tutorial-tip').textContent = step ? step.tip : '';
    
    // Nav buttons
    document.getElementById('tutorial-prev-btn').disabled = tutorialStep <= 0;
    document.getElementById('tutorial-next-btn').disabled = tutorialStep >= total - 1;
}

function renderTutorialStep() {
    if (!tutorialData) return;
    
    clearSolution();
    
    // Render pieces up to current step
    for (let i = 0; i <= tutorialStep; i++) {
        const piece = tutorialData.ordered_pieces[i];
        const color = COLORS[i % COLORS.length];
        const isCurrent = i === tutorialStep;
        
        const group = createPiece(piece, color, i);
        
        // Make current piece more prominent
        if (isCurrent) {
            group.traverse((child) => {
                if (child.material && child.isMesh) {
                    child.material.emissive = new THREE.Color(0x333333);
                }
            });
        } else {
            // Make previous pieces slightly transparent
            group.traverse((child) => {
                if (child.material && child.isMesh) {
                    child.material.opacity = 0.7;
                }
            });
        }
        
        pieceGroups.push(group);
        scene.add(group);
    }
}

function tutorialNext() {
    if (tutorialData && tutorialStep < tutorialData.total_pieces - 1) {
        tutorialStep++;
        updateTutorialUI();
        renderTutorialStep();
    }
}

function tutorialPrev() {
    if (tutorialStep > 0) {
        tutorialStep--;
        updateTutorialUI();
        renderTutorialStep();
    }
}

function startTutorial() {
    if (!tutorialData) {
        loadTutorial().then(() => {
            if (tutorialData) {
                tutorialStep = 0;
                updateTutorialUI();
                renderTutorialStep();
            }
        });
    } else {
        tutorialStep = 0;
        updateTutorialUI();
        renderTutorialStep();
    }
}

function toggleAutoPlay() {
    if (autoPlayInterval) {
        stopAutoPlay();
    } else {
        startAutoPlay();
    }
}

function startAutoPlay() {
    const btn = document.getElementById('auto-play-btn');
    btn.textContent = '⏹ Stop';
    btn.classList.add('playing');
    
    if (!tutorialData) {
        loadTutorial().then(() => {
            if (tutorialData) {
                tutorialStep = 0;
                renderTutorialStep();
                autoPlayInterval = setInterval(() => {
                    if (tutorialStep < tutorialData.total_pieces - 1) {
                        tutorialNext();
                    } else {
                        stopAutoPlay();
                    }
                }, 800); // 800ms per piece
            }
        });
    } else {
        autoPlayInterval = setInterval(() => {
            if (tutorialStep < tutorialData.total_pieces - 1) {
                tutorialNext();
            } else {
                stopAutoPlay();
            }
        }, 800);
    }
}

function stopAutoPlay() {
    if (autoPlayInterval) {
        clearInterval(autoPlayInterval);
        autoPlayInterval = null;
    }
    const btn = document.getElementById('auto-play-btn');
    btn.textContent = '▶ Auto Play';
    btn.classList.remove('playing');
}

// =============================================================================
// PATTERNS MODE
// =============================================================================

async function loadPatterns() {
    if (!isServerOnline) return;
    
    try {
        const response = await fetch('/api/patterns');
        if (response.ok) {
            patternsData = await response.json();
            renderPatternsList();
        }
    } catch (e) {
        console.error('Failed to load patterns:', e);
    }
}

function renderPatternsList() {
    if (!patternsData) return;
    
    const container = document.getElementById('patterns-list');
    container.innerHTML = '';
    
    for (const pattern of patternsData.patterns) {
        const card = document.createElement('div');
        card.className = 'pattern-card';
        card.dataset.patternId = pattern.id;
        
        card.innerHTML = `
            <div class="pattern-name">
                ${pattern.name}
                <span class="pattern-difficulty ${pattern.difficulty}">${pattern.difficulty}</span>
            </div>
            <div class="pattern-desc">${pattern.description}</div>
            <div class="pattern-tip">💡 ${pattern.tip}</div>
        `;
        
        card.addEventListener('click', () => {
            // Update active state
            document.querySelectorAll('.pattern-card').forEach(c => c.classList.remove('active'));
            card.classList.add('active');
            
            // Render the pattern
            renderPattern(pattern);
        });
        
        container.appendChild(card);
    }
}

function renderPattern(pattern) {
    clearSolution();
    
    // Render each piece in the pattern
    pattern.pieces.forEach((piece, i) => {
        const color = COLORS[i % COLORS.length];
        const group = createPiece(piece, color, i);
        pieceGroups.push(group);
        scene.add(group);
    });
    
    // Adjust camera to focus on the pattern
    const allCells = pattern.pieces.flat();
    if (allCells.length > 0) {
        const centerX = allCells.reduce((s, c) => s + c[0], 0) / allCells.length;
        const centerY = allCells.reduce((s, c) => s + c[1], 0) / allCells.length;
        const centerZ = allCells.reduce((s, c) => s + c[2], 0) / allCells.length;
        
        controls.target.set(centerX, centerY, centerZ);
        camera.position.set(centerX + 8, centerY + 8, centerZ + 8);
        controls.update();
    }
}

// =============================================================================
// EXTENDED UI SETUP
// =============================================================================

function setupModeListeners() {
    // Mode tabs
    document.querySelectorAll('.mode-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            setMode(tab.dataset.mode);
        });
    });
    
    // Tutorial controls
    document.getElementById('tutorial-prev-btn').addEventListener('click', tutorialPrev);
    document.getElementById('tutorial-next-btn').addEventListener('click', tutorialNext);
    document.getElementById('tutorial-start-btn').addEventListener('click', startTutorial);
    document.getElementById('auto-play-btn').addEventListener('click', toggleAutoPlay);
    
    // Keyboard shortcuts for tutorial
    document.addEventListener('keydown', (e) => {
        if (currentMode === 'tutorial') {
            if (e.key === 'ArrowRight' || e.key === ' ') {
                tutorialNext();
                e.preventDefault();
            } else if (e.key === 'ArrowLeft') {
                tutorialPrev();
                e.preventDefault();
            }
        }
    });
}

// Call setup after DOM is ready
setTimeout(setupModeListeners, 100);

// =============================================================================
// START
// =============================================================================

init();
