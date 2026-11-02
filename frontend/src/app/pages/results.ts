import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../core/auth';
import { ApiService, Meta, downloadBlob, readableError } from '../core/api';
@Component({standalone:true,imports:[CommonModule,FormsModule],template:`
<div class="page-heading"><div><span class="eyebrow">ACADEMIC PERFORMANCE</span><h1>Examination Results</h1><p>Review subject-wise marks, grades and downloadable report cards.</p></div></div>
@if(message()){<div class="alert alert-danger">{{message()}}</div>}
<div class="panel filters-panel"><div class="filter-grid"><div><label class="form-label">Student</label><select class="form-select" [(ngModel)]="studentId" [disabled]="auth.role()==='student'" (ngModelChange)="result.set(null)"><option [ngValue]="0">Select student</option>@for(s of students();track s.id){<option [ngValue]="s.id">{{s.name}} ({{s.code}})</option>}</select></div><div><label class="form-label">Examination</label><select class="form-select" [(ngModel)]="examId" (ngModelChange)="result.set(null)"><option [ngValue]="0">Select examination</option>@for(e of meta().examinations;track e.id){<option [ngValue]="e.id">{{e.name}}</option>}</select></div><div class="filter-action"><button class="btn btn-primary" [disabled]="!studentId||!examId" (click)="load()">View Result</button></div></div></div>
@if(result()){<div class="report-sheet"><div class="report-header"><div><span class="eyebrow">OFFICIAL REPORT CARD</span><h2>SANKALP CLASSES</h2><p>Student Academic Performance Report</p></div><button class="btn btn-outline-primary" (click)="download()"><i class="bi bi-file-earmark-pdf"></i> Download PDF</button></div>
<div class="report-info"><div><small>STUDENT NAME</small><strong>{{result().student.full_name}}</strong></div><div><small>STUDENT ID</small><strong>{{result().student.code}}</strong></div><div><small>EXAMINATION</small><strong>{{result().exam.name}}</strong></div><div><small>ACADEMIC YEAR</small><strong>{{result().exam.academic_year}}</strong></div></div>
<div class="table-responsive"><table class="table modern-table"><thead><tr><th>Subject</th><th>Obtained</th><th>Maximum</th><th>Percentage</th><th>Grade</th><th>Status</th></tr></thead><tbody>@for(s of result().subjects;track s.subject_id){<tr><td>{{s.subject}}</td><td>{{s.obtained===null?'—':s.obtained}}</td><td>{{s.max_marks}}</td><td>{{s.percentage===null?'—':s.percentage+'%'}}</td><td><strong>{{s.grade}}</strong></td><td>{{s.passed?'Pass':'Not Passed'}}</td></tr>}</tbody></table></div>
<div class="result-summary"><div><small>OVERALL SCORE</small><h2>{{result().obtained}} / {{result().maximum}}</h2></div><div><small>PERCENTAGE</small><h2>{{result().percentage}}%</h2></div><div><small>GRADE</small><h2>{{result().grade}}</h2></div><div><small>RESULT</small><h2>{{result().status}}</h2></div></div></div>}
@else{<div class="panel empty-state">Choose a student and exam to view the report card. Students can only access published results.</div>}
`})
export class ResultsPage implements OnInit{
 auth=inject(AuthService);private api=inject(ApiService);meta=signal<Meta>({classes:[],batches:[],subjects:[],teachers:[],students:[],examinations:[]});studentId=0;examId=0;
 result=signal<any>(null);message=signal('');
 students(){return this.meta().students;}
 ngOnInit(){if(this.auth.role()==='student'){
    this.api.get<any>('results/available').subscribe({next:r=>{this.meta.update(m=>({...m,students:[r.student],examinations:r.examinations}));this.studentId=r.student.id;},error:e=>this.message.set(readableError(e))});
  }else{this.api.get<Meta>('meta').subscribe({next:r=>this.meta.set(r),error:e=>this.message.set(readableError(e))});}}
 load(){this.api.get<any>(`results/${this.studentId}/${this.examId}`).subscribe({next:r=>{this.result.set(r.result);this.message.set('');},error:e=>{this.result.set(null);this.message.set(readableError(e));}});}
 download(){this.api.blob(`results/${this.studentId}/${this.examId}/pdf`).subscribe({next:b=>downloadBlob(b,`sankalp-result-${this.studentId}-${this.examId}.pdf`),error:e=>this.message.set(readableError(e))});}
}
