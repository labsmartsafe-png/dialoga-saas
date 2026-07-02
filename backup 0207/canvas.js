/**
 * canvas.js - Canvas visual moderno com zoom, pan, minimap e menu de conexão.
 */

(function (global) {
  const NODE_WIDTH = 200;
  const NODE_HEIGHT = 90;
  const GRID_SIZE = 20;
  const MIN_ZOOM = 0.25;
  const MAX_ZOOM = 2.5;

  let connecting = null;
  let dragging = null;
  let panning = null;
  let zoom = 1;
  let panX = 0;
  let panY = 0;
  let spacePressed = false;

  function snapToGrid(value) {
    return Math.round(value / GRID_SIZE) * GRID_SIZE;
  }

  function getCurrentPositions(nodes) {
    const positions = {};
    nodes.forEach(function (n) {
      const el = document.getElementById("canvas-node-" + n.id);
      if (el) {
        positions[n.id] = {
          x: parseInt(el.style.left, 10) || 0,
          y: parseInt(el.style.top, 10) || 0,
        };
      } else {
        positions[n.id] = { x: n.position_x || 0, y: n.position_y || 0 };
      }
    });
    return positions;
  }

  function calculateAutoLayout(nodes) {
    if (!nodes || !nodes.length) return {};
    const childrenOf = {};
    nodes.forEach(function (n) { childrenOf[n.id] = []; });
    nodes.forEach(function (n) {
      if (n.next && childrenOf[n.next]) childrenOf[n.id].push(n.next);
      if (n.options) n.options.forEach(function (opt) {
        if (opt.next && childrenOf[opt.next]) childrenOf[n.id].push(opt.next);
      });
      if (n.condition && n.condition.next && childrenOf[n.condition.next]) {
        childrenOf[n.id].push(n.condition.next);
      }
      if (n.fallback && childrenOf[n.fallback]) {
        childrenOf[n.id].push(n.fallback);
      }
    });
    const depths = {};
    const roots = nodes.filter(function (n) { return !hasParent(n, nodes); });
    const queue = roots.map(function (n) { return { id: n.id, depth: 0 }; });
    while (queue.length) {
      const item = queue.shift();
      if (depths[item.id] !== undefined && depths[item.id] <= item.depth) continue;
      depths[item.id] = item.depth;
      (childrenOf[item.id] || []).forEach(function (c) {
        queue.push({ id: c, depth: item.depth + 1 });
      });
    }
    const positions = {};
    const byDepth = {};
    Object.keys(depths).forEach(function (id) {
      const d = depths[id];
      if (!byDepth[d]) byDepth[d] = [];
      byDepth[d].push(id);
    });
    Object.keys(byDepth).forEach(function (depth) {
      byDepth[depth].forEach(function (id, i) {
        positions[id] = {
          x: 50 + depth * (NODE_WIDTH + 280),
          y: 50 + i * (NODE_HEIGHT + 40),
        };
      });
    });
    return positions;
  }

  function hasParent(node, allNodes) {
    return allNodes.some(function (other) {
      if (other.id === node.id) return false;
      if (other.next === node.id) return true;
      if (other.options && other.options.some(function (opt) { return opt.next === node.id; })) return true;
      if (other.condition && other.condition.next === node.id) return true;
      if (other.fallback === node.id) return true;
      return false;
    });
  }

  function renderNodes(nodes, onSelect, onMove, onConnect) {
    const layer = document.getElementById("nodes-layer");
    const empty = document.getElementById("canvas-empty");
    if (!layer) return;

    if (!nodes || !nodes.length) {
      layer.innerHTML = "";
      if (empty) empty.style.display = "block";
      clearConnections();
      return;
    }
    if (empty) empty.style.display = "none";

    const autoLayout = calculateAutoLayout(nodes);
    const positions = {};

    nodes.forEach(function (n) {
      if (n.position_x !== null && n.position_x !== undefined &&
          n.position_y !== null && n.position_y !== undefined) {
        positions[n.id] = { x: n.position_x, y: n.position_y };
      } else if (autoLayout[n.id]) {
        positions[n.id] = autoLayout[n.id];
      } else {
        positions[n.id] = { x: 50, y: 50 };
      }
    });

    // FIX: Persistir posições de volta nos objetos (evita sobreposição ao re-renderizar)
    nodes.forEach(function (n) {
      if (positions[n.id]) {
        n.position_x = positions[n.id].x;
        n.position_y = positions[n.id].y;
      }
    });

    expandCanvas(positions, nodes.length);
    layer.innerHTML = "";

    const colors = {
      message: "linear-gradient(135deg, #06b6d4, #0891b2)",
      question: "linear-gradient(135deg, #7c3aed, #6d28d9)",
      input: "linear-gradient(135deg, #f59e0b, #d97706)",
      condition: "linear-gradient(135deg, #8b5cf6, #7c3aed)",
      delay: "linear-gradient(135deg, #6b7280, #4b5563)",
      webhook: "linear-gradient(135deg, #0891b2, #0e7490)",
      human: "linear-gradient(135deg, #4338ca, #3730a3)",
      end: "linear-gradient(135deg, #ef4444, #dc2626)",
    };

    nodes.forEach(function (n) {
      const pos = positions[n.id];
      const div = document.createElement("div");
      div.className = "canvas-node";
      div.id = "canvas-node-" + n.id;
      div.style.left = pos.x + "px";
      div.style.top = pos.y + "px";
      div.dataset.nodeId = n.id;
      const color = colors[n.type] || "#6b7280";

      div.innerHTML =
        '<div class="node-header">' +
          '<span class="node-type" style="background:' + color + '">' + n.type + '</span>' +
        '</div>' +
        '<div class="node-content">' + escapeHtml((n.content || n.id).slice(0, 60)) + '</div>' +
        '<div class="node-id">' + escapeHtml(n.id) + '</div>' +
        '<div class="canvas-node-port input" data-node-id="' + n.id + '" data-port="input"></div>' +
        '<div class="canvas-node-port output" data-node-id="' + n.id + '" data-port="output"></div>';

      div.addEventListener("mousedown", function (e) {
        if (e.target.classList.contains("canvas-node-port")) return;
        if (e.button !== 0) return;
        startNodeDrag(e, n.id, div, nodes, onMove);
      });

      div.addEventListener("click", function (e) {
        if (dragging && dragging.moved) return;
        if (e.target.classList.contains("canvas-node-port")) return;
        e.stopPropagation();
        layer.querySelectorAll(".canvas-node").forEach(function (el) {
          el.classList.remove("selected");
        });
        div.classList.add("selected");
        if (onSelect) onSelect(n.id);
      });

      layer.appendChild(div);
    });

    layer.querySelectorAll(".canvas-node-port.output").forEach(function (port) {
      port.addEventListener("mousedown", function (e) {
        e.stopPropagation();
        e.preventDefault();
        startConnect(e, port.dataset.nodeId, nodes, onConnect);
      });
    });

    layer.querySelectorAll(".canvas-node-port.input").forEach(function (el) {
      el.addEventListener("mouseover", function () {
        if (connecting) el.classList.add("target-highlight");
      });
      el.addEventListener("mouseout", function () {
        el.classList.remove("target-highlight");
      });
    });

    drawConnections(nodes, positions);
    renderMinimap(nodes, positions);
    applyTransform();
  }

  function expandCanvas(positions, count) {
    const inner = document.getElementById("canvas-inner");
    const svg = document.getElementById("connections-svg");
    if (!inner || !svg) return;
    let maxX = 3000, maxY = 2000;
    Object.keys(positions).forEach(function (id) {
      const p = positions[id];
      if (p.x + 250 > maxX) maxX = p.x + 500;
      if (p.y + 150 > maxY) maxY = p.y + 500;
    });
    inner.style.width = maxX + "px";
    inner.style.height = maxY + "px";
    svg.setAttribute("width", maxX);
    svg.setAttribute("height", maxY);
  }

  function startNodeDrag(e, nodeId, element, allNodes, onMove) {
    e.preventDefault();
    e.stopPropagation();
    const startX = e.clientX, startY = e.clientY;
    const startLeft = parseInt(element.style.left, 10) || 0;
    const startTop = parseInt(element.style.top, 10) || 0;
    dragging = { nodeId: nodeId, element: element, startX: startX, startY: startY, startLeft: startLeft, startTop: startTop, moved: false };
    function onMove2(ev) {
      const dx = (ev.clientX - startX) / zoom;
      const dy = (ev.clientY - startY) / zoom;
      if (Math.abs(dx) > 3 / zoom || Math.abs(dy) > 3 / zoom) dragging.moved = true;
      element.style.left = snapToGrid(startLeft + dx) + "px";
      element.style.top = snapToGrid(startTop + dy) + "px";
      redrawConnections(allNodes, getCurrentPositions(allNodes));
      renderMinimap(allNodes, getCurrentPositions(allNodes));
    }
    function onUp2() {
      document.removeEventListener("mousemove", onMove2);
      document.removeEventListener("mouseup", onUp2);
      if (dragging && dragging.moved) {
        const newLeft = parseInt(element.style.left, 10) || 0;
        const newTop = parseInt(element.style.top, 10) || 0;
        if (onMove) onMove(nodeId, newLeft, newTop);
      }
      dragging = null;
    }
    document.addEventListener("mousemove", onMove2);
    document.addEventListener("mouseup", onUp2);
  }

  function startConnect(e, fromNodeId, allNodes, onConnect) {
    const wrapper = document.getElementById("canvas-wrapper");
    if (wrapper) wrapper.classList.add("connecting");
    const positions = getCurrentPositions(allNodes);
    const fromPos = positions[fromNodeId];
    const rect = wrapper.getBoundingClientRect();
    connecting = {
      fromNodeId: fromNodeId,
      tempX: (e.clientX - rect.left + wrapper.scrollLeft) / zoom - panX / zoom,
      tempY: (e.clientY - rect.top + wrapper.scrollTop) / zoom - panY / zoom,
    };
    function onMove2(ev) {
      if (!connecting) return;
      const r = wrapper.getBoundingClientRect();
      connecting.tempX = (ev.clientX - r.left + wrapper.scrollLeft) / zoom - panX / zoom;
      connecting.tempY = (ev.clientY - r.top + wrapper.scrollTop) / zoom - panY / zoom;
      drawTempLine(allNodes);
      document.querySelectorAll(".target-highlight").forEach(function (el) {
        el.classList.remove("target-highlight");
      });
      const targetEl = document.elementFromPoint(ev.clientX, ev.clientY);
      if (targetEl && targetEl.classList.contains("canvas-node-port") &&
          targetEl.dataset.port === "input" && targetEl.dataset.nodeId !== fromNodeId) {
        targetEl.classList.add("target-highlight");
      }
    }
    function onUp2(ev) {
      document.removeEventListener("mousemove", onMove2);
      document.removeEventListener("mouseup", onUp2);
      if (wrapper) wrapper.classList.remove("connecting");
      const targetEl = document.elementFromPoint(ev.clientX, ev.clientY);
      if (targetEl && targetEl.classList.contains("canvas-node-port") &&
          targetEl.dataset.port === "input") {
        const toNodeId = targetEl.dataset.nodeId;
        if (toNodeId !== fromNodeId && onConnect) {
          onConnect(fromNodeId, toNodeId);
        }
      }
      const tempLine = document.getElementById("temp-connection-line");
      if (tempLine) tempLine.remove();
      connecting = null;
    }
    document.addEventListener("mousemove", onMove2);
    document.addEventListener("mouseup", onUp2);
  }

  function drawTempLine(allNodes) {
    if (!connecting) return;
    const svg = document.getElementById("connections-svg");
    if (!svg) return;
    let line = document.getElementById("temp-connection-line");
    if (!line) {
      line = document.createElementNS("http://www.w3.org/2000/svg", "path");
      line.id = "temp-connection-line";
      line.setAttribute("stroke", "#8b5cf6");
      line.setAttribute("stroke-width", "3");
      line.setAttribute("stroke-dasharray", "6,4");
      line.setAttribute("fill", "none");
      line.setAttribute("vector-effect", "non-scaling-stroke");
      svg.querySelector("#connections-group").appendChild(line);
    }
    const positions = getCurrentPositions(allNodes);
    const from = positions[connecting.fromNodeId];
    if (!from) return;
    const startX = from.x + NODE_WIDTH;
    const startY = from.y + NODE_HEIGHT / 2;
    line.setAttribute("d", createSmoothPath(startX, startY, connecting.tempX, connecting.tempY));
  }

  // ============ NOVO: Menu suspenso da conexão ============
  function showConnectionMenu(mouseEvent, fromId, target) {
    // Remove menu existente
    closeConnectionMenu();

    const menu = document.createElement("div");
    menu.id = "connection-menu";
    menu.className = "connection-menu";

    // Posiciona no clique do mouse
    menu.style.left = mouseEvent.clientX + "px";
    menu.style.top = mouseEvent.clientY + "px";

    // Ajusta se sair da tela
    setTimeout(function () {
      const rect = menu.getBoundingClientRect();
      if (rect.right > window.innerWidth) {
        menu.style.left = (window.innerWidth - rect.width - 10) + "px";
      }
      if (rect.bottom > window.innerHeight) {
        menu.style.top = (window.innerHeight - rect.height - 10) + "px";
      }
    }, 0);

    const nodeTypes = [
      { type: "message", icon: "💬", label: "Mensagem" },
      { type: "question", icon: "❓", label: "Pergunta" },
      { type: "input", icon: "✏️", label: "Entrada de texto" },
      { type: "condition", icon: "🔀", label: "Condição" },
      { type: "delay", icon: "⏱️", label: "Espera / Delay" },
      { type: "webhook", icon: "🔗", label: "Webhook" },
      { type: "human", icon: "👤", label: "Atendimento humano" },
      { type: "end", icon: "🏁", label: "Fim de fluxo" },
    ];

    menu.innerHTML =
      '<div class="cm-header">Inserir nó entre</div>' +
      nodeTypes.map(function (nt) {
        return '<div class="cm-item" data-insert-type="' + nt.type + '">' +
          '<span class="cm-icon">' + nt.icon + '</span>' + nt.label +
          '</div>';
      }).join("") +
      '<div class="cm-divider"></div>' +
      '<div class="cm-item cm-danger" data-delete-conn="1">' +
        '<span class="cm-icon">🗑️</span> Excluir conexão' +
      '</div>';

    document.body.appendChild(menu);

    // Handler: inserir nó
    menu.querySelectorAll("[data-insert-type]").forEach(function (item) {
      item.addEventListener("click", function () {
        if (global.WFCanvas && global.WFCanvas.onInsertNodeBetween) {
          global.WFCanvas.onInsertNodeBetween(fromId, target, item.dataset.insertType);
        }
        closeConnectionMenu();
      });
    });

    // Handler: excluir conexão
    const delBtn = menu.querySelector("[data-delete-conn]");
    if (delBtn) {
      delBtn.addEventListener("click", function () {
        if (global.WFCanvas && global.WFCanvas.onRemoveConnection) {
          global.WFCanvas.onRemoveConnection(fromId, target);
        }
        closeConnectionMenu();
      });
    }

    // Fecha ao clicar fora (depois de um tick para não fechar imediatamente)
    setTimeout(function () {
      document.addEventListener("mousedown", onOutsideClick);
    }, 0);
  }

  function onOutsideClick(e) {
    const menu = document.getElementById("connection-menu");
    if (menu && !menu.contains(e.target)) {
      closeConnectionMenu();
    }
  }

  function closeConnectionMenu() {
    const menu = document.getElementById("connection-menu");
    if (menu) menu.remove();
    document.removeEventListener("mousedown", onOutsideClick);
  }

  // ============ Desenho das conexões (CORRIGIDO) ============
  function drawConnections(nodes, positions) {
    const group = document.getElementById("connections-group");
    if (!group) return;
    group.innerHTML = "";

    nodes.forEach(function (n) {
      const targets = collectTargets(n);
      targets.forEach(function (target) {
        if (!positions[n.id] || !positions[target.id]) return;

        const from = {
          x: positions[n.id].x + NODE_WIDTH,
          y: positions[n.id].y + NODE_HEIGHT / 2,
        };

        let to, marker, className, strokeColor;

        if (target.type === "option") {
          to = {
            x: positions[target.id].x,
            y: positions[target.id].y + 20 + target.index * 16,
          };
          marker = "url(#arrowhead-option)";
          className = "option";
          strokeColor = "#10b981";
        } else if (target.type === "condition") {
          to = {
            x: positions[target.id].x,
            y: positions[target.id].y + NODE_HEIGHT / 2,
          };
          marker = "url(#arrowhead-condition)";
          className = "condition";
          strokeColor = "#f59e0b";
        } else {
          to = {
            x: positions[target.id].x,
            y: positions[target.id].y + NODE_HEIGHT / 2,
          };
          marker = "url(#arrowhead)";
          className = "";
          strokeColor = "#8b5cf6";
        }

        const pathData = createSmoothPath(from.x, from.y, to.x, to.y);

        // ============ PATH VISÍVEL ============
        const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
        path.setAttribute("d", pathData);
        path.setAttribute("marker-end", marker);
        path.setAttribute("data-from", n.id);
        path.setAttribute("data-to", target.id);
        path.setAttribute("data-type", target.type);
        // FIX: cor sólida como fallback + gradient via style
        path.setAttribute("stroke", strokeColor);
        path.setAttribute("stroke-width", "3");
        path.setAttribute("fill", "none");
        path.setAttribute("opacity", "0.85");        if (className) path.setAttribute("class", className);
        path.style.cursor = "pointer";
        path.style.pointerEvents = "stroke";

        // ============ PATH INVISÍVEL (área de clique ampla) ============
        const hitPath = document.createElementNS("http://www.w3.org/2000/svg", "path");
        hitPath.setAttribute("d", pathData);
        hitPath.setAttribute("stroke", "transparent");
        hitPath.setAttribute("stroke-width", "24");
        hitPath.setAttribute("fill", "none");
        hitPath.setAttribute("vector-effect", "non-scaling-stroke");
        hitPath.style.cursor = "pointer";
        hitPath.style.pointerEvents = "stroke";
        hitPath.setAttribute("data-from", n.id);
        hitPath.setAttribute("data-to", target.id);

        // ============ BOTÃO "+" NO MEIO ============
        const midpoint = getPathMidpoint(from.x, from.y, to.x, to.y);
        const plusGroup = document.createElementNS("http://www.w3.org/2000/svg", "g");
        plusGroup.setAttribute("class", "connection-plus");
        plusGroup.setAttribute("transform", "translate(" + midpoint.x + ", " + midpoint.y + ")");
        plusGroup.style.cursor = "pointer";
        plusGroup.style.opacity = "0";
        plusGroup.style.transition = "opacity 0.15s";
        plusGroup.style.pointerEvents = "all";

        const plusCircle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
        plusCircle.setAttribute("r", "12");
        plusCircle.setAttribute("fill", "#fff");
        plusCircle.setAttribute("stroke", "#7c3aed");
        plusCircle.setAttribute("stroke-width", "2");
        plusGroup.appendChild(plusCircle);

        const plusH = document.createElementNS("http://www.w3.org/2000/svg", "line");
        plusH.setAttribute("x1", "-5"); plusH.setAttribute("y1", "0");
        plusH.setAttribute("x2", "5"); plusH.setAttribute("y2", "0");
        plusH.setAttribute("stroke", "#7c3aed");
        plusH.setAttribute("stroke-width", "2");
        plusH.setAttribute("stroke-linecap", "round");
        plusGroup.appendChild(plusH);

        const plusV = document.createElementNS("http://www.w3.org/2000/svg", "line");
        plusV.setAttribute("x1", "0"); plusV.setAttribute("y1", "-5");
        plusV.setAttribute("x2", "0"); plusV.setAttribute("y2", "5");
        plusV.setAttribute("stroke", "#7c3aed");
        plusV.setAttribute("stroke-width", "2");
        plusV.setAttribute("stroke-linecap", "round");
        plusGroup.appendChild(plusV);

        // ============ HOVER ============
        function showPlus() {
          plusGroup.style.opacity = "1";
          path.setAttribute("opacity", "1");
          path.setAttribute("stroke-width", "4");
        }
        function hidePlus() {
          plusGroup.style.opacity = "0";
          path.setAttribute("opacity", "0.75");
          path.setAttribute("stroke-width", "2.5");
        }

        path.addEventListener("mouseenter", showPlus);
        path.addEventListener("mouseleave", hidePlus);
        hitPath.addEventListener("mouseenter", showPlus);
        hitPath.addEventListener("mouseleave", hidePlus);
        plusGroup.addEventListener("mouseenter", showPlus);
        plusGroup.addEventListener("mouseleave", hidePlus);

        // FIX: Clique no "+" abre MENU SUSPENSO (em vez de inserir direto)
        plusGroup.addEventListener("click", function (e) {
          e.stopPropagation();
          e.preventDefault();
          showConnectionMenu(e, n.id, target);
        });

        // Botão direito = remover
        function handleContextMenu(e) {
          e.preventDefault();
          e.stopPropagation();
          showConnectionMenu(e, n.id, target);
        }

        path.addEventListener("contextmenu", handleContextMenu);
        hitPath.addEventListener("contextmenu", handleContextMenu);

        // Ordem: hitPath (atrás) → path (meio) → plusGroup (frente)
        group.appendChild(path);
        group.appendChild(hitPath);
        group.appendChild(plusGroup);
      });
    });
  }

  function redrawConnections(nodes, positions) {
    drawConnections(nodes, positions);
  }

  function collectTargets(n) {
    const targets = [];
    if (n.next) targets.push({ id: n.next, type: "main", label: "" });
    if (n.options) n.options.forEach(function (opt, i) {
      if (opt.next) targets.push({ id: opt.next, type: "option", label: opt.label || "", index: i });
    });
    if (n.condition && n.condition.next) {
      targets.push({ id: n.condition.next, type: "condition", label: "se sim" });
    }
    if (n.fallback) {
      targets.push({ id: n.fallback, type: "condition", label: "se não" });
    }
    return targets;
  }

  function createSmoothPath(x1, y1, x2, y2) {
    const dx = x2 - x1;
    const dy = y2 - y1;

    // Distância horizontal dos pontos de controle
    const cpDist = Math.max(60, Math.abs(dx) * 0.5);

    let cp1y = y1;
    let cp2y = y2;

    // FIX: Quando os nós estão em paralelo (mesma altura), a curva fica
    // degenerada e some. Adicionamos uma curvatura mínima (arco suave)
    // para garantir que a linha seja sempre visível.
    if (Math.abs(dy) < 40) {
      const bow = 14; // arco suave para baixo (estilo n8n)
      cp1y = y1 + bow;
      cp2y = y2 + bow;
    }

    return "M " + x1 + " " + y1 +
           " C " + (x1 + cpDist) + " " + cp1y +
           ", " + (x2 - cpDist) + " " + cp2y +
           ", " + x2 + " " + y2;
  }
  function getPathMidpoint(x1, y1, x2, y2) {
    return { x: (x1 + x2) / 2, y: (y1 + y2) / 2 };
  }

  function clearConnections() {
    const group = document.getElementById("connections-group");
    if (group) group.innerHTML = "";
  }

  // ============ ZOOM ============
  function setZoom(newZoom, centerX, centerY) {
    newZoom = Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, newZoom));
    const wrapper = document.getElementById("canvas-wrapper");
    if (!wrapper) return;
    const oldZoom = zoom;
    zoom = newZoom;
    if (centerX !== undefined && centerY !== undefined) {
      const rect = wrapper.getBoundingClientRect();
      const cx = centerX - rect.left;
      const cy = centerY - rect.top;
      panX = cx - (cx - panX) * (newZoom / oldZoom);
      panY = cy - (cy - panY) * (newZoom / oldZoom);
    }
    applyTransform();
    const zoomLabel = document.getElementById("zoom-level");
    if (zoomLabel) zoomLabel.textContent = Math.round(zoom * 100) + "%";
  }

  function applyTransform() {
    const inner = document.getElementById("canvas-inner");
    if (inner) {
      inner.style.transform = "translate(" + panX + "px, " + panY + "px) scale(" + zoom + ")";
    }
  }

  function initZoomControls() {
    const wrapper = document.getElementById("canvas-wrapper");
    if (!wrapper) return;

    wrapper.addEventListener("wheel", function (e) {
      if (e.ctrlKey || e.metaKey) {
        e.preventDefault();
        const delta = e.deltaY > 0 ? -0.1 : 0.1;
        setZoom(zoom + delta, e.clientX, e.clientY);
      }
    }, { passive: false });

    const btnIn = document.getElementById("btn-zoom-in");
    if (btnIn) btnIn.addEventListener("click", function () { setZoom(zoom + 0.2); });
    const btnOut = document.getElementById("btn-zoom-out");
    if (btnOut) btnOut.addEventListener("click", function () { setZoom(zoom - 0.2); });
    const btnFit = document.getElementById("btn-zoom-fit");
    if (btnFit) btnFit.addEventListener("click", function () { fitToScreen(); });

    wrapper.addEventListener("mousedown", function (e) {
      if (e.button === 1 || (spacePressed && e.button === 0)) {
        e.preventDefault();
        startPan(e);
      }
    });

    document.addEventListener("keydown", function (e) {
      if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") return;
      if (e.code === "Space") {
        spacePressed = true;
        wrapper.style.cursor = "grab";
      }
      if (e.key === "Escape") {
        connecting = null;
        const tempLine = document.getElementById("temp-connection-line");
        if (tempLine) tempLine.remove();
        wrapper.classList.remove("connecting");
        closeConnectionMenu();
      }
    });

    document.addEventListener("keyup", function (e) {
      if (e.code === "Space") {
        spacePressed = false;
        wrapper.style.cursor = "grab";
      }
    });
  }

  function startPan(e) {
    const wrapper = document.getElementById("canvas-wrapper");
    wrapper.classList.add("panning");
    const startX = e.clientX, startY = e.clientY;
    const startPanX = panX, startPanY = panY;
    function onMove2(ev) {
      panX = startPanX + (ev.clientX - startX);
      panY = startPanY + (ev.clientY - startY);
      applyTransform();
    }
    function onUp2() {
      wrapper.classList.remove("panning");
      document.removeEventListener("mousemove", onMove2);
      document.removeEventListener("mouseup", onUp2);
    }
    document.addEventListener("mousemove", onMove2);
    document.addEventListener("mouseup", onUp2);
  }

  function fitToScreen() {
    const wrapper = document.getElementById("canvas-wrapper");
    if (!wrapper) return;
    const inner = document.getElementById("canvas-inner");
    if (!inner) return;
    const nodes = inner.querySelectorAll(".canvas-node");
    if (!nodes.length) {
      setZoom(1);
      panX = 0; panY = 0;
      applyTransform();
      return;
    }
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    nodes.forEach(function (n) {
      const x = parseInt(n.style.left, 10) || 0;
      const y = parseInt(n.style.top, 10) || 0;
      if (x < minX) minX = x;
      if (y < minY) minY = y;
      if (x > maxX) maxX = x;
      if (y > maxY) maxY = y;
    });
    const padding = 100;
    const flowWidth = maxX - minX + NODE_WIDTH + padding * 2;
    const flowHeight = maxY - minY + NODE_HEIGHT + padding * 2;
    const wrapperWidth = wrapper.clientWidth;
    const wrapperHeight = wrapper.clientHeight;
    const newZoom = Math.min(wrapperWidth / flowWidth, wrapperHeight / flowHeight, 1);
    setZoom(newZoom);
    panX = padding - minX * newZoom;
    panY = padding - minY * newZoom;
    applyTransform();
  }

  // ============ MINIMAP ============
  function renderMinimap(nodes, positions) {
    const minimap = document.getElementById("minimap-inner");
    if (!minimap) return;
    minimap.innerHTML = "";
    if (!nodes.length) return;
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    Object.keys(positions).forEach(function (id) {
      const p = positions[id];
      if (p.x < minX) minX = p.x;
      if (p.y < minY) minY = p.y;
      if (p.x + NODE_WIDTH > maxX) maxX = p.x + NODE_WIDTH;
      if (p.y + NODE_HEIGHT > maxY) maxY = p.y + NODE_HEIGHT;
    });
    const flowW = maxX - minX || 1;
    const flowH = maxY - minY || 1;
    const miniW = minimap.clientWidth - 8;
    const miniH = minimap.clientHeight - 8;
    const scale = Math.min(miniW / flowW, miniH / flowH);
    nodes.forEach(function (n) {
      const p = positions[n.id];
      const node = document.createElement("div");
      node.className = "minimap-node";
      node.style.left = (4 + (p.x - minX) * scale) + "px";
      node.style.top = (4 + (p.y - minY) * scale) + "px";
      node.style.width = (NODE_WIDTH * scale) + "px";
      node.style.height = (NODE_HEIGHT * scale) + "px";
      node.title = n.id;
      minimap.appendChild(node);
    });
    const wrapper = document.getElementById("canvas-wrapper");
    if (!wrapper) return;
    const viewW = wrapper.clientWidth / zoom;
    const viewH = wrapper.clientHeight / zoom;
    const viewX = -panX / zoom;
    const viewY = -panY / zoom;
    const viewport = document.createElement("div");
    viewport.className = "minimap-viewport";
    viewport.style.left = (4 + (viewX - minX) * scale) + "px";
    viewport.style.top = (4 + (viewY - minY) * scale) + "px";
    viewport.style.width = (viewW * scale) + "px";
    viewport.style.height = (viewH * scale) + "px";
    minimap.appendChild(viewport);
    minimap.onclick = function (e) {
      const rect = minimap.getBoundingClientRect();
      const clickX = e.clientX - rect.left - 4;
      const clickY = e.clientY - rect.top - 4;
      const flowX = minX + clickX / scale;
      const flowY = minY + clickY / scale;
      panX = -(flowX - wrapper.clientWidth / (2 * zoom)) * zoom;
      panY = -(flowY - wrapper.clientHeight / (2 * zoom)) * zoom;
      applyTransform();
      renderMinimap(nodes, positions);
    };
  }

  function escapeHtml(s) {
    return String(s || "").replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initZoomControls);
  } else {
    initZoomControls();
  }

  global.WFCanvas = {
    renderNodes: renderNodes,
    redrawConnections: redrawConnections,
    fitToScreen: fitToScreen,
    setZoom: setZoom,
    getZoom: function () { return zoom; },
    calculateAutoLayout: calculateAutoLayout,
    onRemoveConnection: null,
    onInsertNodeBetween: null,
  };
})(window);