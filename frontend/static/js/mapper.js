// Diachronic visualisation using D3.js
class DiachronicMapper {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.width = 800;
        this.height = 400;
    }
    
    visualize(path) {
        // Clear previous
        this.container.innerHTML = '';
        
        const svg = d3.select(this.container)
            .append('svg')
            .attr('width', this.width)
            .attr('height', this.height);
        
        // Create nodes from stages
        const nodes = path.stages.map((stage, i) => ({
            id: i,
            form: stage.form,
            period: stage.period,
            change: stage.change,
            x: 100 + (i * (this.width - 200) / (path.stages.length - 1)),
            y: this.height / 2
        }));
        
        // Draw connections
        for (let i = 0; i < nodes.length - 1; i++) {
            svg.append('line')
                .attr('x1', nodes[i].x)
                .attr('y1', nodes[i].y)
                .attr('x2', nodes[i + 1].x)
                .attr('y2', nodes[i + 1].y)
                .attr('stroke', '#CD7F32')
                .attr('stroke-width', 2);
        }
        
        // Draw nodes
        const nodeGroups = svg.selectAll('.node')
            .data(nodes)
            .enter()
            .append('g')
            .attr('class', 'node')
            .attr('transform', d => `translate(${d.x}, ${d.y})`);
        
        nodeGroups.append('circle')
            .attr('r', 30)
            .attr('fill', (d, i) => i === 0 ? '#8B5A2B' : i === nodes.length - 1 ? '#4A90E2' : '#CD7F32');
        
        nodeGroups.append('text')
            .attr('text-anchor', 'middle')
            .attr('dy', 5)
            .attr('fill', 'white')
            .attr('font-weight', 'bold')
            .text(d => d.form);
        
        nodeGroups.append('text')
            .attr('text-anchor', 'middle')
            .attr('dy', 50)
            .attr('font-size', '12px')
            .text(d => d.period);
        
        // Add change labels on arrows
        for (let i = 0; i < nodes.length - 1; i++) {
            if (nodes[i + 1].change) {
                svg.append('text')
                    .attr('x', (nodes[i].x + nodes[i + 1].x) / 2)
                    .attr('y', nodes[i].y - 20)
                    .attr('text-anchor', 'middle')
                    .attr('font-size', '11px')
                    .attr('fill', '#666')
                    .text(nodes[i + 1].change);
            }
        }
    }
}