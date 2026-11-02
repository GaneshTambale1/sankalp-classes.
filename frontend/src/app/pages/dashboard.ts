import { Component, inject, OnInit, signal, ViewChild, ElementRef, AfterViewInit, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { Chart, registerables } from 'chart.js';
import { AuthService } from '../core/auth';
import { ApiService, readableError } from '../core/api';
Chart.register(...registerables);
@Component({selector:'app-attendance-chart',standalone:true,template:`<div class="chart-wrapper"><canvas #canvas></canvas></div>`})
export class AttendanceChartComponent implements AfterViewInit {
 @Input() trend:any[]=[];
 @ViewChild('canvas') canvas!:ElementRef<HTMLCanvasElement>;
 ngAfterViewInit(){const months=[...new Set(this.trend.map(x=>x.month))];new Chart(this.canvas.nativeElement,{type:'line',data:{labels:months,datasets:[{label:'Present',data:months.map(m=>this.trend.find(t=>t.month===m&&t.status==='present')?.count||0),borderColor:'#2563eb',backgroundColor:'#dbeafe',tension:.35,fill:true},{label:'Absent',data:months.map(m=>this.trend.find(t=>t.month===m&&t.status==='absent')?.count||0),borderColor:'#ef4444',tension:.35}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'bottom'}}}});}
}
@Component({standalone:true,imports:[CommonModule,RouterLink,AttendanceChartComponent],template:`
<div class="page-heading"><div><span class="eyebrow">YOUR WORKSPACE</span><h1>Good day, {{auth.user()?.full_name?.split(' ')?.[0]}} <span class="wave">✦</span></h1><p>Here’s what’s happening at Sankalp Classes today.</p></div><div class="today-chip"><i class="bi bi-calendar3"></i> {{today | date:'fullDate'}}</div></div>
@if(error()){<div class="alert alert-danger">{{error()}}</div>}
@if(loading()){<div class="panel p-5">Loading live institute statistics…</div>}
@else {
@if(auth.role()==='admin') {
<div class="stats-grid">@for(stat of adminStats;track stat.key){<div class="stat-card"><div class="stat-icon"><i class="bi {{stat.icon}}"></i></div><small>{{stat.label}}</small><div class="stat-value">{{data()?.stats?.[stat.key]??0}}{{stat.suffix||''}}</div></div>}</div>
<div class="dashboard-grid"><section class="panel"><div class="panel-heading"><h3>Attendance Overview</h3><small>Monthly trend · actual records</small></div>@if(data()?.monthly_attendance?.length){<app-attendance-chart [trend]="data().monthly_attendance"/>}@else{<div class="empty-state">No attendance records recorded yet.</div>}</section><section class="panel"><div class="panel-heading"><h3>Quick Actions</h3><small>Most frequently used tools</small></div><div class="quick-actions"><a routerLink="/manage/students"><i class="bi bi-person-plus"></i> Add Student</a><a routerLink="/attendance"><i class="bi bi-calendar-check"></i> Mark Attendance</a><a routerLink="/manage/examinations"><i class="bi bi-journal-text"></i> Examinations</a><a routerLink="/marks"><i class="bi bi-pencil-square"></i> Enter Marks</a><a routerLink="/reports"><i class="bi bi-download"></i> Export Reports</a></div></section></div>
<div class="dashboard-grid"><section class="panel"><div class="panel-heading"><h3>Recently Admitted</h3></div>@for(s of data()?.recent_students||[];track s.id){<div class="mini-row"><div class="small-avatar">{{s.full_name.charAt(0)}}</div><div><strong>{{s.full_name}}</strong><small>{{s.code}} · Class #{{s.class_id}}</small></div></div>}@if(!data()?.recent_students?.length){<div class="empty-state">No students yet</div>}</section><section class="panel"><div class="panel-heading"><h3>Attendance Attention</h3><small>Below {{data()?.stats?.attendance_warning_threshold||75}}%, at least 3 applicable days</small></div>@for(s of data()?.low_attendance||[];track s.student_id){<div class="mini-row"><div class="small-avatar warning"><i class="bi bi-exclamation"></i></div><div><strong>{{s.name}}</strong><small>{{s.percentage}}% attendance</small></div></div>}@if(!data()?.low_attendance?.length){<div class="empty-state">No low-attendance alerts</div>}</section></div>
} @else if(auth.role()==='teacher'){
<div class="stats-grid"><div class="stat-card"><small>Assigned Batches</small><div class="stat-value">{{data()?.stats?.assigned_batches||0}}</div></div><div class="stat-card"><small>Assigned Subjects</small><div class="stat-value">{{data()?.stats?.assigned_subjects||0}}</div></div><div class="stat-card"><small>My Students</small><div class="stat-value">{{data()?.stats?.students||0}}</div></div></div><div class="panel action-panel"><h3>Teaching Workspace</h3><p>Mark daily attendance, manage your subject’s marks and review results.</p><a routerLink="/attendance" class="btn btn-primary me-2">Attendance</a><a routerLink="/marks" class="btn btn-outline-primary me-2">Enter Marks</a><a routerLink="/results" class="btn btn-outline-primary">Results</a></div>
} @else {<div class="stats-grid"><div class="stat-card"><small>Attendance</small><div class="stat-value">{{data()?.stats?.attendance?.percentage||0}}%</div><p class="muted">{{data()?.stats?.attendance?.present||0}} present · {{data()?.stats?.attendance?.absent||0}} absent</p></div><div class="stat-card"><small>Available Results</small><div class="stat-value">{{data()?.stats?.published_exams||0}}</div></div></div><div class="panel action-panel"><h3>My Academic Progress</h3><p>Track your attendance and published examination results.</p><a routerLink="/attendance" class="btn btn-primary me-2">My Attendance</a><a routerLink="/results" class="btn btn-outline-primary">My Results</a></div>}
}
`})
export class DashboardPage implements OnInit {
 auth=inject(AuthService);private api=inject(ApiService);today=new Date();data=signal<any>(null);loading=signal(true);error=signal('');
 adminStats=[{key:'total_students',label:'Total Students',icon:'bi-people'},{key:'active_students',label:'Active Students',icon:'bi-person-check'},{key:'total_teachers',label:'Teachers',icon:'bi-person-workspace'},{key:'total_classes',label:'Classes',icon:'bi-building'},{key:'total_batches',label:'Batches',icon:'bi-collection'},{key:'today_present',label:'Present Today',icon:'bi-check-circle'},{key:'today_absent',label:'Absent Today',icon:'bi-x-circle'},{key:'attendance_percentage',label:'Attendance Rate',icon:'bi-graph-up',suffix:'%'}];
 ngOnInit(){this.auth.refresh().subscribe({next:()=>this.load(),error:()=>this.loading.set(false)});}
 load(){this.api.get<any>(`dashboard/${this.auth.role()}`).subscribe({next:r=>{this.data.set(r);this.loading.set(false);},error:e=>{this.error.set(readableError(e));this.loading.set(false);}});}
}
