# -*- coding: utf-8 -*-

def get_node_order(dataset, shapes_count):
    if dataset == "LUBM":
        if shapes_count == 3:
            return ['Department',
                    'University',
                    'FullProfessor']
        elif shapes_count == 7:
            return ['ResearchGroup',
                    'Department',
                    'University',
                    'Course',
                    'FullProfessor',
                    'UndergraduateStudent',
                    'Publication']
        elif shapes_count == 14:
            return ['ResearchGroup',
                    'ResearchAssistant',
                    'Department',
                    'University',
                    'Course',
                    'FullProfessor',
                    'AssociateProfessor',
                    'UndergraduateStudent',
                    'Lecturer',
                    'GraduateCourse',
                    'AssistantProfessor',
                    'Publication',
                    'GraduateStudent',
                    'TeachingAssistant']
