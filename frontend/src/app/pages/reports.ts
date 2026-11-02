import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ApiService, downloadBlob, readableError } from '../core/api';
@Component({standalone:true,imports:[FormsModule],template:`<div class="page-heading"><div><span class="eyebrow">REPORTING & INSIGHTS</span><h1>Export Reports</h1><p>Download live attendance and academic records as CSV files.</p></div></div>@if(error()){<div class="alert alert-danger">{{error()}}</div>}
<div class="grid-two"><section class="panel report-card"><div class="report-icon"><i class="bi bi-calendar-check"></i></div><h3>Attendance Report</h3><p class="muted">Daily attendance history with students and recorded statuses.</p><div class="mb-3"><label class="form-label">From Date</label><input class="form-control" type="date" [(ngModel)]="from"></div><div class="mb-3"><label class="form-label">To Date</label><input class="form-control" type="date" [(ngModel)]="to"></div><button class="btn btn-primary" (click)="exportAttendance()"><i class="bi bi-download"></i> Download CSV</button></section><section class="panel report-card"><div class="report-icon"><i class="bi bi-graph-up"></i></div><h3>Academic Marks Report</h3><p class="muted">Export examination, subject, grade and percentage data.</p><button class="btn btn-primary" (click)="exportMarks()"><i class="bi bi-download"></i> Download CSV</button></section></div>`})
export class ReportsPage{
 private api=inject(ApiService);from='';to='';error=signal('');
 exportAttendance(){this.api.blob('reports/attendance.csv',{from:this.from,to:this.to}).subscribe({next:b=>downloadBlob(b,'sankalp-attendance.csv'),error:e=>this.error.set(readableError(e))});}
 exportMarks(){this.api.blob('reports/marks.csv').subscribe({next:b=>downloadBlob(b,'sankalp-marks.csv'),error:e=>this.error.set(readableError(e))});}
}
