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
// START
// =============================================================================

init();
