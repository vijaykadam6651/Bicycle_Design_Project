import * as THREE from "three";

const canvas = document.querySelector("#bike-view");
const fallback = document.querySelector("#viewer-fallback");
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false });
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.setClearColor(0xe8ece6, 1);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0xe8ece6);
const camera = new THREE.PerspectiveCamera(33, 1, 1, 10000);
camera.up.set(0, 0, 1);
const target = new THREE.Vector3(85, 0, 210);
const cameraViews = {
  iso: new THREE.Vector3(1270, -2050, 1120),
  side: new THREE.Vector3(0, -2600, 460),
};
camera.position.copy(cameraViews.iso);
scene.add(new THREE.HemisphereLight(0xffffff, 0x7d8d85, 2.15));
const keyLight = new THREE.DirectionalLight(0xffffff, 2.2);
keyLight.position.set(-450, -800, 1400);
scene.add(keyLight);
const fillLight = new THREE.DirectionalLight(0xffe6d3, 0.7);
fillLight.position.set(800, 650, 400);
scene.add(fillLight);

const grid = new THREE.GridHelper(1800, 36, 0xa6b3aa, 0xcbd3ca);
grid.rotation.x = Math.PI / 2;
grid.position.z = -270;
grid.material.transparent = true;
grid.material.opacity = 0.42;
scene.add(grid);

const materials = {
  frame: new THREE.MeshStandardMaterial({ color: 0x176072, metalness: 0.48, roughness: 0.34 }),
  fork: new THREE.MeshStandardMaterial({ color: 0x247488, metalness: 0.42, roughness: 0.37 }),
  tire: new THREE.MeshStandardMaterial({ color: 0x172125, roughness: 0.88 }),
  rim: new THREE.MeshStandardMaterial({ color: 0xc0c9c4, metalness: 0.72, roughness: 0.28 }),
  spoke: new THREE.LineBasicMaterial({ color: 0x8c9995, transparent: true, opacity: 0.62 }),
  dark: new THREE.MeshStandardMaterial({ color: 0x20292b, metalness: 0.23, roughness: 0.55 }),
  metal: new THREE.MeshStandardMaterial({ color: 0x929e9d, metalness: 0.72, roughness: 0.32 }),
};
const partGroups = new Map();
let activePart = "frame";

function register(mesh, part, title) {
  mesh.material = mesh.material.clone();
  mesh.userData.part = part;
  mesh.userData.title = title;
  if (!partGroups.has(part)) partGroups.set(part, []);
  partGroups.get(part).push(mesh);
  scene.add(mesh);
  return mesh;
}

function tubeBetween(start, end, radius, material, part, title) {
  const a = new THREE.Vector3(...start);
  const b = new THREE.Vector3(...end);
  const direction = new THREE.Vector3().subVectors(b, a);
  const mesh = new THREE.Mesh(new THREE.CylinderGeometry(radius, radius, direction.length(), 12), material);
  mesh.position.copy(a).add(b).multiplyScalar(0.5);
  mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), direction.normalize());
  return register(mesh, part, title);
}

function ringAt(axle, radius, width, material, part, title) {
  const geometry = new THREE.TorusGeometry(radius, width, 9, 96);
  geometry.rotateX(Math.PI / 2);
  const mesh = new THREE.Mesh(geometry, material);
  mesh.position.set(...axle);
  return register(mesh, part, title);
}

function buildWheel(axle, label) {
  const part = "wheels";
  ringAt(axle, 327.5, 12.5, materials.tire, part, `${label} tire envelope`);
  ringAt(axle, 298, 3, materials.rim, part, `${label} rim envelope`);
  for (const side of [-1, 1]) {
    tubeBetween([axle[0], axle[1] + side * 6, axle[2]], [axle[0], axle[1] - side * 6, axle[2]], 8, materials.metal, part, `${label} hub envelope`);
    const points = [];
    for (let spoke = 0; spoke < 16; spoke += 1) {
      const angle = (spoke / 16) * Math.PI * 2;
      points.push(new THREE.Vector3(axle[0] + 24 * Math.cos(angle), axle[1] + side * 27, axle[2] + 24 * Math.sin(angle)));
      points.push(new THREE.Vector3(axle[0] + 291 * Math.cos(angle + side * 0.07), axle[1], axle[2] + 291 * Math.sin(angle + side * 0.07)));
    }
    const geometry = new THREE.BufferGeometry().setFromPoints(points);
    register(new THREE.LineSegments(geometry, materials.spoke), part, `${label} spokes`);
  }
}

function buildModel(data) {
  const { points, frame_members: members } = data;
  for (const member of members) {
    tubeBetween(points[member.start], points[member.end], member.od_mm / 2, materials.frame, "frame", member.name);
  }
  tubeBetween([0, -34, 0], [0, 34, 0], 20, materials.metal, "frame", "Bottom bracket shell");
  buildWheel(points.RearAxle, "Rear");
  buildWheel(points.FrontAxle, "Front");

  for (const side of ["L", "R"]) {
    tubeBetween(points.ForkCrown, points[`ForkShoulder${side}`], 12.5, materials.fork, "fork", "Fork blade");
    tubeBetween(points[`ForkShoulder${side}`], points[`FrontDropout${side}`], 12.5, materials.fork, "fork", "Fork blade");
  }
  tubeBetween(points.HeadUpper, [points.HeadUpper[0] - 14, 0, points.HeadUpper[2] + 48], 14, materials.dark, "fork", "Steerer and stem");
  tubeBetween([points.HeadUpper[0] - 14, 0, points.HeadUpper[2] + 48], [points.HeadUpper[0] + 90, 0, points.HeadUpper[2] + 76], 10, materials.dark, "fork", "Stem envelope");
  tubeBetween([points.HeadUpper[0] + 90, -210, points.HeadUpper[2] + 76], [points.HeadUpper[0] + 90, 210, points.HeadUpper[2] + 76], 12, materials.dark, "fork", "Handlebar envelope");

  const seatTop = points.SeatTop;
  const postTop = [seatTop[0] - 42, 0, seatTop[2] + 142];
  tubeBetween(seatTop, postTop, 12, materials.dark, "frame", "Seatpost envelope");
  tubeBetween([postTop[0] - 68, 0, postTop[2] + 7], [postTop[0] + 88, 0, postTop[2] + 7], 10, materials.dark, "frame", "Saddle envelope");

  ringAt([0, -45, 0], 105, 3, materials.metal, "drive", "Chainring envelope");
  tubeBetween([0, -48, 0], [0, -91, 0], 7, materials.metal, "drive", "Crank spindle");
  for (const side of [-1, 1]) {
    tubeBetween([0, side * 82, 0], [0, side * 82, side * 172.5], 8, materials.dark, "drive", "Crank arm envelope");
    tubeBetween([0, side * 82, side * 172.5], [0, side * 112, side * 172.5], 7, materials.metal, "drive", "Pedal envelope");
  }
  ringAt([points.RearAxle[0], -45, points.RearAxle[2]], 35, 3, materials.metal, "drive", "Rear sprocket envelope");
  setActivePart(activePart);
}

function setActivePart(part) {
  activePart = part;
  for (const [group, meshes] of partGroups) {
    for (const mesh of meshes) {
      if (mesh.material.emissive) mesh.material.emissive.setHex(group === part ? 0x183a2e : 0x000000);
      if (mesh.isLineSegments) mesh.material.color.setHex(group === part ? 0x456f4f : 0x8c9995);
    }
  }
  document.querySelectorAll(".part-button").forEach((button) => {
    const selected = button.dataset.part === part;
    button.classList.toggle("selected", selected);
    button.setAttribute("aria-pressed", String(selected));
  });
  const descriptions = {
    frame: ["Round-tube frame", "Twelve nominal hollow members make up the frame layout. Tube grade, wall sizing and joint details have not been structurally qualified."],
    fork: ["Fork & steering", "The fork, headset and cockpit are concept envelopes in a static assembly. Steering motion and supplier interfaces have not been verified."],
    wheels: ["Wheel envelopes", "The 680 × 25 mm tire shape is a nominal clearance envelope, not a selected or approved tire-and-rim combination."],
    drive: ["Drivetrain envelopes", "The chainring and sprocket are smooth illustrative envelopes. The two chain strands do not model links, shifting or freewheel behavior."],
  };
  document.querySelector("#part-title").textContent = descriptions[part][0];
  document.querySelector("#part-copy").textContent = descriptions[part][1];
}

function changeView(name) {
  camera.position.copy(cameraViews[name]);
  camera.lookAt(target);
  document.querySelectorAll(".view-button").forEach((button) => {
    const selected = button.dataset.view === name;
    button.classList.toggle("active", selected);
    button.setAttribute("aria-pressed", String(selected));
  });
}

let drag = null;
canvas.addEventListener("pointerdown", (event) => {
  drag = { x: event.clientX, y: event.clientY, moved: false };
  canvas.setPointerCapture(event.pointerId);
});
canvas.addEventListener("pointermove", (event) => {
  if (!drag) return;
  const dx = event.clientX - drag.x;
  const dy = event.clientY - drag.y;
  if (Math.abs(dx) + Math.abs(dy) > 2) drag.moved = true;
  drag.x = event.clientX;
  drag.y = event.clientY;
  const spherical = new THREE.Spherical().setFromVector3(camera.position.clone().sub(target));
  spherical.theta -= dx * 0.006;
  spherical.phi = THREE.MathUtils.clamp(spherical.phi + dy * 0.005, 0.15, Math.PI - 0.15);
  camera.position.copy(target).add(new THREE.Vector3().setFromSpherical(spherical));
  camera.lookAt(target);
});
canvas.addEventListener("pointerup", (event) => {
  if (drag && !drag.moved) {
    const bounds = canvas.getBoundingClientRect();
    const pointer = new THREE.Vector2(((event.clientX - bounds.left) / bounds.width) * 2 - 1, -((event.clientY - bounds.top) / bounds.height) * 2 + 1);
    const raycaster = new THREE.Raycaster();
    raycaster.setFromCamera(pointer, camera);
    const hit = raycaster.intersectObjects([...partGroups.values()].flat())[0];
    if (hit?.object.userData.part) setActivePart(hit.object.userData.part);
  }
  drag = null;
});
canvas.addEventListener("pointercancel", () => { drag = null; });
canvas.addEventListener("wheel", (event) => {
  event.preventDefault();
  const offset = camera.position.clone().sub(target).multiplyScalar(1 + Math.sign(event.deltaY) * 0.08);
  camera.position.copy(target).add(offset.normalize().multiplyScalar(THREE.MathUtils.clamp(offset.length(), 1000, 4300)));
  camera.lookAt(target);
}, { passive: false });

document.querySelectorAll(".part-button").forEach((button) => button.addEventListener("click", () => setActivePart(button.dataset.part)));
document.querySelectorAll(".view-button").forEach((button) => button.addEventListener("click", () => changeView(button.dataset.view)));
document.querySelector("#reset-view").addEventListener("click", () => changeView("iso"));

function resize() {
  const { width, height } = canvas.getBoundingClientRect();
  if (!width || !height) return;
  renderer.setSize(width, height, false);
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
}
new ResizeObserver(resize).observe(canvas);
window.addEventListener("resize", resize);
resize();

function animate() {
  renderer.render(scene, camera);
  requestAnimationFrame(animate);
}

async function loadProjectData() {
  const [parametersResponse, validationResponse] = await Promise.all([
    fetch("04_Reference_Data/design_parameters.json"),
    fetch("04_Reference_Data/validation_results.json"),
  ]);
  if (!parametersResponse.ok || !validationResponse.ok) throw new Error("Project data unavailable");
  const [parameters, validation] = await Promise.all([parametersResponse.json(), validationResponse.json()]);
  document.querySelectorAll("[data-param]").forEach((element) => {
    const value = parameters.parameters[element.dataset.param];
    if (value !== undefined) element.textContent = `${value}${element.tagName === "DD" ? " mm" : ""}`;
  });
  document.querySelectorAll("[data-derived]").forEach((element) => {
    const value = parameters.derived[element.dataset.derived];
    if (value !== undefined) element.textContent = `${Number(value).toFixed(1)} mm`;
  });
  const clearances = validation.checks.filter((check) => /tire to (chainstays|seatstays|seat tube|down tube|fork)/i.test(check.check));
  const chart = document.querySelector("#clearance-bars");
  const max = 30;
  chart.replaceChildren(...clearances.map((check) => {
    const row = document.createElement("div");
    row.className = "clearance-row";
    const label = document.createElement("span");
    label.textContent = check.check.replace(" to ", " / ");
    const track = document.createElement("div");
    track.className = "bar-track";
    const bar = document.createElement("i");
    bar.style.setProperty("--bar", `${Math.min(check.measured_mm / max * 100, 100)}%`);
    const targetLine = document.createElement("b");
    targetLine.style.setProperty("--target", `${check.target_mm / max * 100}%`);
    track.append(bar, targetLine);
    const value = document.createElement("strong");
    value.textContent = `${Number(check.measured_mm).toFixed(2)} mm`;
    row.append(label, track, value);
    return row;
  }));
  buildModel(parameters);
  fallback.classList.remove("visible");
  animate();
}

loadProjectData().catch(() => {
  canvas.style.display = "none";
  fallback.classList.add("visible");
});