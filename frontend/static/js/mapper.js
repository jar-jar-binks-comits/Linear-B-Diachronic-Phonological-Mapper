/**
 * VERTICAL DIACHRONIC MAPPER - Timeline visualization
 * Shows evolution from top (Mycenaean) to bottom (Classical)
 */

class DiachronicMapper {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error(`Container ${containerId} not found`);
            return;
        }
        
        this.width = options.width || 400;
        this.height = options.height || 550;
        this.layout = options.layout || 'vertical';
        
        // Professional dark palette
        this.colors = {
            mycenaean: '#5C4033',
            intermediate: '#8B6914', 
            classical: '#1a4d7a',
            connection: '#7a7a7a',
            text: '#2c2c2c',
            background: '#fafafa'
        };
    }
    
    clear() {
        if (this.container) {
            this.container.innerHTML = '';
        }
    }
    
    visualize(data) {
        if (!this.container) return;
        
        this.clear();
        
        const stages = data.stages || [];
        if (stages.length < 2) {
            this.container.innerHTML = '<div class="no-data">No evolution data</div>';
            return;
        }
        
        // VERTICAL TIMELINE LAYOUT
        const svg = d3.select(this.container)
            .append('svg')
            .attr('width', this.width)
            .attr('height', this.height)
            .style('background', this.colors.background);
        
        // Calculate vertical positions
        const margin = { top: 40, right: 40, bottom: 40, left: 40 };
        const usableHeight = this.height - margin.top - margin.bottom;
        const stepHeight = usableHeight / (stages.length - 1);
        const centerX = this.width / 2;
        
        const nodes = stages.map((stage, i) => ({
            form: stage.form,
            period: stage.period,
            change: stage.change || '',
            x: centerX,
            y: margin.top + (i * stepHeight),
            index: i,
            isFirst: i === 0,
            isLast: i === stages.length - 1
        }));
        
        // Draw connection lines
        for (let i = 0; i < nodes.length - 1; i++) {
            svg.append('line')
                .attr('x1', nodes[i].x)
                .attr('y1', nodes[i].y + 35)
                .attr('x2', nodes[i + 1].x)
                .attr('y2', nodes[i + 1].y - 35)
                .attr('stroke', this.colors.connection)
                .attr('stroke-width', 3)
                .attr('stroke-dasharray', '5,5')
                .attr('opacity', 0.5);
        }
        
        // Draw nodes
        const nodeGroups = svg.selectAll('.node')
            .data(nodes)
            .enter()
            .append('g')
            .attr('class', 'timeline-node')
            .attr('transform', d => `translate(${d.x}, ${d.y})`);
        
        // Node circles
        nodeGroups.append('circle')
            .attr('r', 32)
            .attr('fill', d => {
                if (d.isFirst) return this.colors.mycenaean;
                if (d.isLast) return this.colors.classical;
                return this.colors.intermediate;
            })
            .attr('stroke', '#ffffff')
            .attr('stroke-width', 3)
            .style('filter', 'drop-shadow(0 2px 6px rgba(0,0,0,0.25))');
        
        // Form text inside circle
        nodeGroups.append('text')
            .attr('text-anchor', 'middle')
            .attr('dy', 5)
            .attr('fill', 'white')
            .attr('font-size', '15px')
            .attr('font-weight', 'bold')
            .text(d => d.form.length > 9 ? d.form.substring(0, 7) + '...' : d.form);
        
        // Period label to the right
        nodeGroups.append('text')
            .attr('x', 50)
            .attr('dy', 5)
            .attr('fill', this.colors.text)
            .attr('font-size', '11px')
            .attr('font-weight', '500')
            .text(d => {
                // Extract just the date range
                const match = d.period.match(/\d{3,4}[^)]+BCE/);
                return match ? match[0] : d.period.split(' ').slice(0, 2).join(' ');
            });
        
        // Stage label to the left
        nodeGroups.append('text')
            .attr('x', -50)
            .attr('dy', 5)
            .attr('text-anchor', 'end')
            .attr('fill', this.colors.mycenaean)
            .attr('font-size', '10px')
            .attr('font-weight', 'bold')
            .attr('text-transform', 'uppercase')
            .text(d => {
                if (d.isFirst) return 'START';
                if (d.isLast) return 'CLASSICAL';
                return `STAGE ${d.index}`;
            });
        
        // Change annotations between nodes
        for (let i = 0; i < nodes.length - 1; i++) {
            if (!nodes[i + 1].change) continue;
            
            const midY = (nodes[i].y + nodes[i + 1].y) / 2;
            const changeText = nodes[i + 1].change;
            
            // Background box
            svg.append('rect')
                .attr('x', centerX - 140)
                .attr('y', midY - 12)
                .attr('width', 280)
                .attr('height', 24)
                .attr('fill', 'white')
                .attr('stroke', this.colors.connection)
                .attr('stroke-width', 1.5)
                .attr('rx', 4);
            
            // Change text
            svg.append('text')
                .attr('x', centerX)
                .attr('y', midY + 4)
                .attr('text-anchor', 'middle')
                .attr('font-size', '11px')
                .attr('fill', this.colors.text)
                .attr('font-weight', '600')
                .text('→ ' + (changeText.length > 38 ? changeText.substring(0, 36) + '...' : changeText));
        }
        
        // Title at top
        svg.append('text')
            .attr('x', centerX)
            .attr('y', 20)
            .attr('text-anchor', 'middle')
            .attr('font-size', '13px')
            .attr('font-weight', 'bold')
            .attr('fill', this.colors.mycenaean)
            .text('PHONOLOGICAL EVOLUTION');
        
        // Legend at bottom
        if (data.changes && data.changes.length > 0) {
            svg.append('text')
                .attr('x', centerX)
                .attr('y', this.height - 10)
                .attr('text-anchor', 'middle')
                .attr('font-size', '10px')
                .attr('fill', '#999')
                .text(`${data.changes.length} sound change${data.changes.length > 1 ? 's' : ''} applied`);
        }
    }
}