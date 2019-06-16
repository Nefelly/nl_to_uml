# coding: utf-8
import time
import datetime
import sys
from flask import request
from hendrix.conf import setting
from ..service import (
    AliOssService,
    GlobalizationService,
    TokenBucketService
)
from ..model import (
    PalmResult
)
sys.path.append('/data/opencv-3.3.0/build/palmprint_classification/pyboostcvconverter/build/')
import cv2
import pbcvt


palm_type = 'palm_type'
life = 'life'
wisdom = 'wisdom'
emotion = 'emotion'
fate = 'fate'
solar = 'solar'

desc = {

    GlobalizationService.REGION_TH: {
        palm_type: [
            u"มือของคุณคือมือประเภทดิน มือดินเป็น สัญลักษณ์ของ การมีเหตุมีผล คุณเป็นคนที่ทำงานสอดคล้องกับความเป็นจริงและมีประสิทธิภาพ มีความซื่อสัตย์ เต็มเปี่ยมไปด้วยความรู้ ทำให้ผู้อื่นรู้สึกถึงความนอบน้อมจริงใจ ถึงแม้ว่าจะไม่เก่งในการใช้คำพูดแสดงความรู้สึก แต่ความซื่อตรงของคุณก็ทำให้เพื่อนๆรู้สึกได้ถึงความอบอุ่น ซึ่งหมายถึงคุณเป็นคนที่สามารถพึ่งพาได้ ",
            u"มือของคุณคือมือประเภทลม มือลมเป็น สัญลักษณ์ขอ ความสามารถด้านการสื่อสาร ชื่นชอบอะไรใหม่ๆและและสิ่งที่น่าตื่นเต้นเร้าใจ มีความยืนหยุ่น คุณเป็นคนฉลาดและมีสติปัญญา ชอบคบค้าสมาคม ในด้านของการเลือกคบคนนั้นมาตราฐานของคุณค่อนข้างสูง คุณยึดมั่นในความรู้สึกของตนเอง บวกกับมาตราฐานที่ค่อนข้างสูงแล้ว จึงทำให้เพศตรงข้ามของคุณเป็นคนที่ค่อนข้างจะมีระดับ ",
            u"มือของคุณคือมือประเภทไฟ มือไฟเป็นสัญลักษณ์ของการเต็มเปี่ยมไปด้วยพลัง คุณเป็นใจร้อนและกระตือรือร้น คุณชอบที่จะทำตัวยุ่งและ มีสิ่งที่อยากทำอยู่เสมอ คุณมักจะรู้จักวิธีดูแลผู้อื่น และสามารถเข้ากับคนอื่นได้ง่าย เมื่อคุณรักใครคุณก็จะซื่อสัตย์กับคนนั้น เนื่องจากคุณเป็นคนที่มักจะใช้พลังงานเยอะ ดังนั้นคุณควรพักผ่อนให้เพียงพอ ",
            u"มือของคุณคือมือประเภทน้ำ เป็นสัญลักษณ์ของความรู้สึก เต็มเปี่ยมไปด้วยความรักและ ปัญญาเป็นเลิศ คุณเป็นคนอ่อนไหวและโรแมนติกทางอารมณ์และการใช้ชีวิต ในด้านความสัมพันธ์มักจะเต็มไปด้วยความคาดหวัง และจินตนาการ แต่คุณต้องระวังคนไม่ดีจะนำความอ่อนโยนของคุณไปใช้ทำร้ายคุณ           "
        ],
        life: [
            u"เส้นชีวิตของคุณลึกและชัดเจน ทั้งหมดนี้แสดงให้เห็นว่าคุณมีร่างกายที่แข็งแรงรวมถึงมีพละกำลัง ในขณะเดียวกันพลังงานและการฟื้นฟูของคุณก็ดีมากๆ ในด้านของลักษณะนิสัยเป็นคนสุขุมรอบคอบ ชอบคบค้าสมาคมและทำให้พวกเขารู้สึกถึงพลังอันแข็งแกร่งของคุณ ",
            u"เส้นชีวิตของคุณลึกและชัดเจน ทั้งหมดนี้แสดงให้เห็นว่าคุณมีร่างกายที่แข็งแรงรวมถึงมีพละกำลัง ในขณะเดียวกันพลังงานและการฟื้นฟูของคุณก็ดีมากๆ ในด้านของลักษณะนิสัยเป็นคนสุขุมรอบครอบ รักครอบครัว แต่ก็ต้องระวังอย่าใช้เวลากับคนในครอบครัว และคำพูดของเพื่อนมากเกินไป",
            u"เส้นชีวิตของคุณราบเรียบและเรียบง่าย คุณต้องระมัดระวังเรื่องสุขภาพ บำรุงรักษาสุขภาพและพละกำลัง ในด้านของลักษณะนิสัยเป็นคนสุขุมรอบครอบ ชอบคบค้าสมาคมและทำให้พวกเขารู้สึกถึงพลังของคุณ ",
            u"เส้นชีวิตของคุณราบเรียบและเรียบง่าย คุณต้องระมัดระวังด้านสุขภาพ บำรุงรักษาสุขภาพและพละกำลัง ในด้านของลักษณะนิสัย คนเป็นคนรักครอบครัว แต่ต้องระวังอย่าใช้เวลากับคนในครอบครัวและคำพูดของเพื่อนมากเกินไป ",
            u"เส้นชีวิตของคุณลึกและชัดเจน ทั้งหมดนี้แสดงให้เห็นว่าคุณมีร่างกายที่แข็งแรงรวมถึงมีพละกำลัง ในขณะเดียวกันพลังงานและการฟื้นฟูของคุณก็ดีมากๆ ในด้านของลักษณะนิสัย เป็นตัวของตัวเอง กล้าหาญและรักการผจญภัย ชอบคบหาสมาคมและทำให้พวกเขารู้สึกถึงพลังของคุณ ",
            u"เส้นชีวิตของคุณลึกและชัดเจน ทั้งหมดนี้แสดงให้เห็นว่าคุณมีร่างกายที่แข็งแรงรวมถึงมีพละกำลัง ขณะเดียวกันพลังงานและการฟื้นฟูของคุณก็ดีมากๆ ในด้านของลักษณะนิสัย เป็นตัวของตัวเอง กล้าหาญและรักการผจญภัย คุณเป็นคนรักครอบครัว แต่ต้องระวังอย่าใช้เวลากับคนในครอบครัวและคำพูดของเพื่อนมากเกินไป ",
            u"เส้นชีวิตของคุณเรียบง่ายและราบเรียบ คุณต้องระมัดระวังด้านสุขภาพ บำรุงรักษาสุขภาพและพละกำลัง ในด้านของลักษณะนิสัย เป็นตัวของตัวเอง กล้าหาญและรักการผจญภัย ชอบคบหาสมาคมและทำให้พวกเขารู้สึกถึงพลังของคุณ ",
            u"เส้นชีวิตของคุณเรียบง่ายและราบเรียบ คุณต้องระมัดระวังด้านสุขภาพ บำรุงรักษาสุขภาพและพละกำลัง ในด้านของลักษณะนิสัย เป็นตัวของตัวเอง กล้าหาญและรักการผจญภัย  คุณเป็นคนรักครอบครัว แต่ต้องระวังอย่าใช้เวลากับคนในครอบครัวและคำพูดของเพื่อนมากเกินไป "
        ],
        wisdom: [
            u"เส้นปัญญาของคุณลึกและชัดเจน แสดงให้เห็นว่าคุณเป็นนักคิดที่ปราดเปรียว ไม่เพียงแต่ความคิดที่ฉลาดเฉลียว และยังตัดสินใจอย่างมีเหตุผลและถูกต้องอีกด้วย มีความเข้าใจที่ยอดเยี่ยม  ในขณะเดียวคุณสามารถมีสมาธิในการทำงานเป็นเวลานาน ปรับตัวเก่ง  ชอบการเปลี่ยนแปลง ขี้สงสัย มีความสนใจหลายๆอย่าง",
            u"เส้นปัญญาของคุณลึกและชัดเจน แสดงให้เห็นว่าคุณเป็นนักคิดที่ปราดเปรียว ไม่เพียงแต่ความคิดที่ฉลาดเฉลียว และยังตัดสินใจอย่างมีเหตุผลและถูกต้องอีกด้วย มีความเข้าใจที่ยอดเยี่ยม  ในขณะเดียวกันคุณสามารถมีสมาธิในการทำงานเป็นเวลานาน ทำงานตามสถานการณ์ความเป็นจริง เป้าหมายชัดเจน สามารถทำงานได้อย่างเต็มศักยาภาพ",
            u"เส้นปัญญาของคุณราบเรียบและเรียบง่าย  แสดงให้เห็นว่าคุณเป็นคนอ่อยไหว เน้นการสื่อสารทางอารมณ์ อุดมไปด้วยจินตนาการ ในขณะเดียวคุณสามารถมีสมาธิในการทำงานเป็นเวลานาน ปรับตัวเก่ง  ชอบการเปลี่ยนแปลง ขี้สงสัย มีความสนใจหลายๆอย่าง",
            u"เส้นปัญญาของคุณราบเรียบและเรียบง่าย  แสดงให้เห็นว่าคุณเป็นคนอ่อนไหว เน้นการสื่อสารทางอารมณ์ อุดมไปด้วยจินตนาการ ทำงานตามสถานการณ์ความเป็นจริง เป้าหมายชัดเจน สามารถทำงานได้อย่างเต็มศักยาภาพ"
        ],
        emotion: [
            u"เส้นอารมณ์ของคุณชัดเจนมาก แสดงให้เห็นว่าคุณเป็นคนมั่นใจในตนเองสูง อบอุ่นและใจกว้างอีกด้วย ความต้องการทางเพศสูง หนักแน่นในความรู้สึก ชอบที่จะเป็นผู้นำ มักจะเป็นผู้เริ่มความสัมพันธ์ก่อนเสมอ กระตือรือร้น มีชีวิตชีวา ความสุขทางกายเป็นเงื่อนไขที่จำเป็นสำหรับคุณในความสัมพันธ์",
            u"เส้นอารมณ์ของคุณชัดเจนมาก แสดงให้เห็นว่าคุณเป็นคนมั่นใจในตนเองสูง อบอุ่นและใจกว้างอีกด้วย เมื่อพูดถึงด้านความรู้สึก คุณกระตือรือร้นและฉลาด ไม่รีบร้อนที่จะมีความรัก จะมีการพิจารณาที่รอบครอบ และอดทนรอคนที่ใช่ คุณมักจะเกิดจากมิตรภาพค่อย ๆพัฒนาไปสู่ความรัก",
            u"เส้นอารมณ์ของคุณราบเรียบและเรียบง่าย คุณมักจะประสบปัญหาทางอารมณ์และทำให้คุณไม่มีความสุข มันง่ายที่จะทำลายความสัมพันธ์ของกันและกัน เพราะความไม่แน่นอนและความไม่สบายใจของคุณ คุณต้องการที่จะยังคงแสวงหาความเชื่อมั่นจากคู่ของคุณ เป็นความใคร่ที่รุนแรง ในขณะเดียวกันคูณมีอารมณ์ที่ค่อนข้างรุนแรง ชอบที่จะเป็นผู้นำ มักจะเป็นผู้เริ่มความสัมพันธ์ก่อนเสมอ กระตือรือร้น มีชีวิตชีวา ความสุขทางกายเป็นเงื่อนไขที่จำเป็นสำหรับคุณในความสัมพันธ์",
            u"เส้นอารมณ์ของคุณราบเรียบและเรียบง่าย คุณมักจะประสบปัญหาทางอารมณ์และทำให้คุณไม่มีความสุข มันง่ายที่จะทำลายความสัมพันธ์ของกันและกัน เพราะความไม่แน่นอนและความไม่สบายใจของคุณ คุณต้องการที่จะยังคงแสวงหาความเชื่อมั่นจากคู่ของคุณ เมื่อพูดถึงด้านความรู้สึก คุณกระตือรือร้นและฉลาด ไม่รีบร้อนที่จะมีความรัก จะมีการพิจารณาที่รอบครอบ และอดทนรอคนที่ใช่ คุณมักจะเกิดจากมิตรภาพค่อย ๆพัฒนาไปสู่ความรัก"
        ],
        fate: [
            u"เส้นชะตากรรมของคุณมองเห็นได้อย่างชัดเจน แสดงให้เห็นว่าคุณมีแรงผลักดันตนเองสูง มีความรู้ที่กว้างไกล เป็นคนที่น่าเชื่อถือ ในขณะเดียวกันก็มีความเป็นผู้นำสูง ทำสิ่งต่างๆอย่างจริงจัง สามารถที่จะควบคุมชะตากรรมของตัวเอง",
            u"เส้นชะตากรรมของคุณไม่ชัดเจนนัก แสดงให้เห็นว่าชีวิตมีความผันผวน การเปลี่ยนแปลงในสภาพแวดล้อมทำให้คุณสับสน คุณไม่ชอบการผูกมัด จะมีชีวิตตามกฎของตัวเอง คิดแง่บวกแล้วชีวิตของคุณจะดี",
        ],
        solar: [
            u"เส้นดวงอาทิตย์ของคุณลึกและชัดเจน แสดงให้เห็นว่า นิสัยของคุณมีเสน่ห์ นิสัยนั้นอบอุ่นเหมือนดวงอาทิตย์ มองโลกในแง่ดี เป็นคนมีโชค เกิดมาพร้อมกับพรสวรรค์ ตราบใดที่คุณอยู่ถูกที่ถูกเวลาคุณจะประสบความสำเร็จ",
            u"เส้นดวงอาทิตย์ของคุณไม่ค่อยชัดเจน แสดงให้เห็นว่าตอนนี้คุณกำลังไม่สบายใจ สำหรับความสุขและความสบายใจแม้ว่ามันจะยังไม่มาถึง ตราบใดที่คุณเชื่อมั่น คุณก็จะประสบความสำเร็จ  "
        ]
    },
    GlobalizationService.REGION_VN: {
        palm_type: [
            u"Tay của bạn thuộc tay mệnh thổ, bạn là mẫu người lí trí, thành thực, hiểu biết rộng, chân thành, mặc dù không biết thể hiện tình cảm nhưng sự trung trực của bạn làm mọi người yên tâm và tin tưởng bạn.",
            u"Tay của bạn thuộc tay mệnh phong, cho thấy bạn là người có năng lực giao tiếp tốt ,là mẫu người thích sự mới mẻ và thử thách. Bạn thông minh, có quan hệ rộng, tiêu chuẩn tìm người yêu khá cao. Bạn có khả năng kiềm chế cảm xúc rất tốt, đồng thời là tuýp người lý tưởng trong mắt người khác.",
            u"Tay của bạn thuộc tay mệnh hỏa, bạn là mẫu người có sinh lực dồi dào, nhiệt tình hồ hởi, luôn thích bận rộn, làm không hết việc, biết quan tâm và hòa đồng với mọi người xung quanh, trong tình yêu là người chung thủy. Do bình thường hay hoạt động quá sức, nên cần chú ý nghỉ ngơi điều dưỡng cơ thế.",
            u"Tay của bạn thuộc tay mệnh thủy, bạn là tuýp người cảm tính, có tài hoa và lòng nhân ái. Bạn khá nhạy cảm trong chuyện tình cảm, là con người lãng mạn nhưng cần chú ý đừng quá thật thà sẽ dễ bị người khác lợi dụng."
        ],
        life: [
            u"Đường sinh mệnh của bạn đậm và rõ nét, cắt với đường trí tuệ cho thấy bạn có thể chất rất tốt, tinh lực dồi dào, khả năng chịu được áp lực và phục hồi nhanh, tính tình bạn khá trầm ổn, luôn muốn tạo dựng các mối quan hệ tốt đẹp hơn.",
            u"Đường sinh mệnh của bạn đậm và rõ nét, cắt với đường trí tuệ cho thấy bạn có thể chất rất tốt, sinh lực dồi dào, có khả năng chịu được áp lực và phục hồi nhanh, tính tình trầm ổn, yêu gia đình, nên chủ động tâm sự nhiều hơn với người thân và bạn bè.",
            u"Đường sinh mệnh của bạn khá mềm mại, nên thường xuyên vận động thể thao, giữ gìn sức khỏe, tính tình bạn trầm ổn, thận trọng, luôn muốn tạo dựng các mối quan hệ tốt đẹp hơn.",
            u"Đường sinh mệnh của bạn khá mềm mại, nên thường xuyên vận động thể thao, giữ gìn sức khỏe, tính tình trầm ổn, yêu gia đình, nên chủ động tâm sự nhiều hơn với người thân và bạn bè.",
            u"Đường sinh mệnh của bạn đậm và rõ nét , giao với đường trí tuệ cho thấy bạn có thể chất rất tốt, sinh lực dồi dào, có khả năng chịu áp lực và phục hồi cao, có tính độc lập, thích mạo hiểm, luôn muốn tạo dựng các mối quan hệ tốt đẹp hơn.",
            u"Đường sinh mệnh của bạn đậm và rõ nét, giao với đường trí tuệ cho thấy bạn có thể chất rất tốt, sinh lực dồi dào, khả năng chịu áp lực cao và phục hồi nhanh, có tính độc lập, ưa mạo hiểm, yêu gia đình, nên chủ động tâm sự nhiều hơn với người thân và bạn bè.",
            u"Đường sinh mệnh của bạn khá mềm mại, nên thường xuyên vận động thể thao, giữ gìn sinh lực, có tính độc lập, ưa mạo hiểm, luôn muốn tạo dựng các mối quan hệ tốt đẹp hơn.",
            u"Đường sinh mệnh của bạn khá mềm mại, nên thường xuyên vận động thể thao, giữ gìn sinh lực, có tính độc lập, thích mạo hiểm, yêu gia đình, nên chủ động tâm sự nhiều hơn với người thân và bạn bè."
        ],
        wisdom: [
            u"Đường trí tuệ của bạn đậm và rõ nét cho thấy bạn là con người có tư tưởng linh hoạt, tư duy nhanh nhẹn, khả năng liên tưởng thực tế rất logic, có tính quyết đoán, khả năng tiếp thu nhanh, chú tâm trong công việc, khả năng thích ứng tốt, thích tìm tòi học hỏi.",
            u"Đường trí tuệ của bạn đậm và rõ nét cho thấy bạn là con người có tư tưởng linh hoạt, tư duy nhanh nhẹn, khả năng liên tưởng thực tế rất logic, có tính quyết đoán, khả năng tiếp thu nhanh, chú tâm trong công việc, làm việc luôn dựa vào tình hình thực tế, mục tiêu rõ ràng, có khả năng phát huy tiềm lực của bản thân trong một số lĩnh vực nhất định.",
            u"Đường trí tuệ của bạn mềm mại cho thấy bạn là người cảm tính, chú trọng về những mối quan hệ tình cảm, trí tưởng tượng phong phú, năng lực thích ứng cao, thích thay đổi, luôn muốn tìm tòi học hỏi. Nhưng bạn nên chú ý chủ động sắp xếp trước mọi kế hoạch.",
            u"Đường trí tuệ của bạn mềm mại cho thấy bạn là người cảm tính, chú trọng về những mối quan hệ tình cảm, trí tưởng tượng phong phú, làm việc luôn dựa vào tình hình thực tế, có mục tiêu rõ ràng, có khả năng phát huy tiềm lực của bản thân trong một số lĩnh vực nhất định."
        ],
        emotion: [
            u"Đường tình cảm của bạn rất sắc nét, cho thấy bạn là người rất tự tin, tính tình khẳng khái, tốt bụng quan tâm mọi người. Bạn là người thích chủ động trong các mối quan hệ, nhiệt tình, tràn đầy sinh lực, chuyện chăn gối là điều kiện cần thiết trong mối quan hệ thân mật.",
            u"Đường tình cảm của bạn rất sắc nét, cho thấy bạn là người rất tự tin, tính tình khẳng khái, tốt bụng quan tâm mọi người. Khi yêu bạn có cái nhìn sắc bén, biết nhẫn nại, suy nghĩ thấu đáo và có xu hướng tình yêu xuất phát từ tình bạn.",
            u"Đường tình cảm của bạn khá mềm mại, cho thấy bạn thường gặp khó khăn về vấn đề tình cảm, bất an và dễ bị ảnh hưởng dẫn tới sự đổ vỡ trong các mối quan hệ. Bạn luôn hy vọng người bên cạnh sẽ mang lại cho mình cảm giác an toàn. Bạn là người thích chủ động trong các mối quan hệ, nhiệt tình, tràn đầy sinh lực, chuyện chăn gối là điều kiện cần thiết trong mối quan hệ thân mật.",
            u"Đường tình cảm của bạn mềm mại cho thấy bạn thường gặp khó khăn về vấn đề tình cảm, bất an và dễ bị ảnh hưởng dẫn tới sự đổ vỡ trong các mối quan hệ. Bạn luôn hy vọng người bên cạnh sẽ mang lại cho mình cảm giác an toàn. Khi yêu bạn có cái nhìn sắc bén , biết nhẫn nại, suy nghĩ thấu đáo và có xu hướng tình yêu xuất phát từ tình bạn."
        ],
        fate: [
            u"Đường vận mệnh của bạn rất đậm và hiếm gặp, cho thấy bạn là người có khả năng tạo động lực cao, kiến thức học rộng biết nhiều, là người rất đáng tin cậy, có khả năng làm lãnh đạo, chăm chỉ làm việc, tự nắm bắt được vận mệnh của bản thân.",
            u"Đường vận mệnh của bạn không rõ nét, cho thấy cuộc sống của bạn khá mệt mỏi, môi trường hiện tại làm bạn cảm thấy bất ổn, bạn không muốn gò bó bởi những lễ nghĩa phép tắc, mà muốn sống theo ý mình. Bạn chỉ cần giữ vững lập trường đúng đắn thì cuộc sống của bạn sẽ đầy thú vị."
        ],
        solar: [
            u"Đường thái dương của bạn đậm và rõ nét, cho thấy con người bạn rất có sức lôi cuốn, bạn rực rỡ như ánh nắng mặt trời, lạc quan, luôn hướng ngoại, bạn có quý nhân phù trợ, gặp nhiều may mắn và dễ đạt được thành công trong cuộc sống.",
            u"Đường thái dương của bạn không rõ nét, cho thấy hiện tại bạn đang gặp phải những điều không vui. Dù hiện tại bạn vẫn chưa vui vẻ và hạnh phúc, nhưng chỉ cần cố gắng tự tin vào bản thân thì sẽ đạt được điều mình mong muốn."
        ]
    },
    GlobalizationService.REGION_EN: {
        palm_type: [
            u'Your basic attribute is "earth", and this type of hand is a symbol of rationality、down-to-earth and have the ability of execution. You are honest, rich in common sense, and let others feel you are sincere. Although you are not good at expressing your feelings in words, your loyalty will make your friends feel pragmatic and can be relied upon.',
            u'''Your basic attribute is "wind", and this type of hand is a symbol of strong communication ability、like fresh and exciting、flexible and active. You are smart and wise, and you have a wide range of contacts. In selecting intimate partners, the screening criteria are very high. You have very stable emotions, and the higher standards will make the opposite sex feel very noble.''',
            u'''Your basic attribute is "fire", and this type of hand is a symbol of energy、impulsiveness and enthusiasm. You like to be busy, always hope that you have something to do, usually know how to care for others, and it's easy for you to make friends with others. If you are making a boyfriend or girlfriend, once you have stabilized, you will be a loyal and enthusiastic lover. Because you usually spend too much physical strength, you should pay attention to maintaining proper rest and sleep.''',
            u'Your basic attribute is "water", and this type of hand is a symbol of sensuality、talent and full of love. You feel sensitive and romantic in your feelings and life, and you are full of ideals for intimate relationships, but be aware that being too gentle is easy to be used by ruthless people.',
        ],
        life: [
            u'Your life line is deep and clear, and coincides with the starting point of the wisdom line. All of these show that you have a great body 、 plenty of energy 、 strong pressure resistance  and good at recovering.  you are cautious in character, be willing to interact with others actively and let them feel your animated',
            u'Your life line is deep and clear, and coincides with the starting point of the wisdom line. All of these show that you have a great body 、 plenty of energy 、 strong pressure resistance  and good at recovering.  you are cautious in character and loving family very much, but you should  pay more time  to communicate with your family and friends about your inner thoughts.',
            u'Your lifel ine is smooth and smooth, and you should pay attention to exercise and keep your vitality. you are cautious in character, be willing to interact with others actively and let them feel your animated',
            u'Your life line is smooth and smooth, and you should pay attention to exercise and keep your vitality.  you are cautious in character and loving family very much, but you should  pay more time  to communicate with your family and friends about your inner thoughts.',
            u'Your life line is deep and clear, and coincides with the starting point of the wisdom line. All of these show that you have a great body 、 plenty of energy 、 strong pressure resistance  and good at recovering.  You are independent in character, take risks, be willing to interact with others actively and let them feel your animated',
            u'Your life line is deep and clear, and coincides with the starting point of the wisdom line. All of these show that you have a great body 、 plenty of energy 、 strong pressure resistance  and good at recovering.  You are independent in character, take risks and loving family very much, but you should  pay more time  to communicate with your family and friends about your inner thoughts.',
            u'Your life line is smooth and smooth, and you should pay attention to exercise and keep your vitality.   You are independent in character, take risks, be willing to interact with others actively and let them feel your animated',
            u'Your life line is smooth and smooth, and you should pay attention to exercise and keep your vitality.   You are independent in character, take risks and loving family very much, but you should  pay more time  to communicate with your family and friends about your inner thoughts.'
        ],
        wisdom: [
            u'Your wisdom line is deep and clear, which shows that you are a flexible thinker. Not only is your mind agile, the factual association is logical, and the decisions you make are more rational and correct, you can concentrate on working for a long time and have  excellent understanding . you have strong adaptability、wide range of interests、 like change and love to ask questions ',
            u'Your wisdom line is deep and clear, which shows that you are a flexible thinker. Not only is your mind agile, the factual association is logical, and the decisions you make are more rational and correct, you can concentrate on working for a long time and have excellent understanding . you like making plan base on the actual situation with a clear goal , and you can realize your potential in a certain field fully',
            u'Your wisdom line is smooth and smooth, which shows that you are a sentimental person, paying attention to emotional communication, you are rich in imagination , you have strong adaptability、wide range of interests、 like change and love to ask questions , but also pay attention to implementation plan  early',
            u'Your wisdom line is smooth and smooth, which shows that you are a sentimental person, paying attention to emotional communication, you are rich in imagination. you like making plan base on the actual situation with a clear goal , and you can realize your potential in a certain field fully'
        ],
        emotion: [
            u'Your emotional line is very clear, indicating that you are confident in your emotions, at the same time  you are warm and generous to others, have strong sexual desires and emotionally dominant , prefer to lead, you are usually the first to take action in sexual relationships. you are Passion、energy， and physical pleasure are necessary conditions for you in intimacy',
            u'Your emotional line is very clear, indicating that you are confident in your emotions, at the same time  you are warm and generous to others,  When it comes to feelings, you are sharp and intelligent, and you are not eager to jump into love. There will be more deliberation: consistent with passive appearance, you like to develop from friendship to love.',
            u'''Your emotional line is smooth and smooth. You may encounter emotional problems or make you feel unhappy. It is easy to destroy each other's relationship because of uncertainty and uneasiness. You want to constantly seek assurance from your partner. you have strong sexual desires and emotionally dominant , prefer to lead, you are usually the first to take action in sexual relationships. you are Passion、energy， and physical pleasure are necessary conditions for you in intimacy''',
            u'''Your emotional line is smooth and smooth. You may encounter emotional problems or make you feel unhappy. It is easy to destroy each other's relationship because of uncertainty and uneasiness. You want to constantly seek assurance from your partner.   When it comes to feelings, you are sharp and intelligent, and you are not eager to jump into love. There will be more deliberation: consistent with passive appearance, you like to develop from friendship to love.''',
        ],
        fate: [
            u'Your line of destiny is very clear, indicating that you are very strong in driving yourself, have a wide range of insights, you are a very trustworthy person, At the same time , you have a leadership temperament and are seriously on working, and be able to control your own destiny.',
            u'Your line of destiny is not very obvious, indicating that life gives you a lot of volatility, environmental changes make you unable to settle, you do not want to be bound by tradition, you will live according to your own rules. As long as you keep thinking, your life will be different.'
        ],
        solar: [
            u'Your sun line is deep and clear, indicating that your character is very attractive, your temperament is warm like sunshine, optimistic and outgoing, have a good luck, and innate talent, as long as you can get great success in right time and place.',
            u'Your sun line is not very obvious, indicating that the existing situation makes you dissatisfied.  Although happiness has not arrived yet, as long as you firmly believe, you will succeed.'
        ]
    },
    GlobalizationService.REGION_ID: {
        palm_type: [
            u"Tangan Anda memiliki elemen tanah, yang berarti Anda adalah orang yang realistis, sederhana dan memiliki kemampuan untuk melakukan sesuatu.  Anda jujur, kaya akan pengetahuan dan ini akan membuat orang disekitar Anda merasa nyaman.m Meskipun Anda tidak pandai mengungkapkan perasaan Anda dengan kata-kata, namum keperibadian Anda dapat membuat teman-teman Anda merasa nyaman berteman dengan Anda dan Anda adalah orang yang dapat diandalkan.",
            u"Tangan Anda memiliki elemen angin, dan tipe tangan angin adalah simbol kemampuan berkomunikasi yang kuat, menyukai hal yang segar dan menantang, fleksibel dan aktif.  Anda pintar dan bijaksana, dan Anda memiliki banyak relasi.  Dalam memilih pasangan, Anda memiliki standar yang tinggi.Anda memiliki emosi yang sangat stabil, dan ditambah dengan standar Anda yang  tinggi akan membuat lawan jenis merasa sangat beruntung memiliki Anda.",
            u"Tangan Anda adalah tangan api, tangan api adalah simbol energi, impulsif, dan antusiasme.  Anda menyukai kesibukkan dan selalu berharap untuk memiliki sesuatu untuk dikerjakan,  biasanya tahu cara memperhatikan orang lain, dan mudah berteman dengan orang lain.  Jika Anda adalah memiliki pasangan, ketika hubungan sudah stabil, Anda akan menjadi kekasih yang setia karena Anda biasanya menghabiskan terlalu banyak waktu untuk mengerjakan kesibukkan Anda, jadi Anda harus memperhatikan istirahat dan tidur yang cukup.",
            u"Tangan Anda adalah tangan air, dan tangan air adalah simbol dari sensualitas, bakat, dan penuh akan cinta.  Anda adalah orang yang sensitif dan romantis dalam perasaan dan Anda berharap untuk mempunyai suatu hubungan yang dekat, tetapi sadarlah bahwa menjadi terlalu lembut akan membuat Anda dimanfaatkan orang lain."
            ],
        life: [
            u"Garis hidup Anda dalam dan jelas, dan bertepatan dengan titik awal dari garis kebijaksanaan. Semua ini menunjukkan bahwa Anda memiliki kondisi kesehatan yang sangat baik. Anda adalah orang yang sangat berhati-hati dan inisiatif untuk berinteraksi dengan orang lain .",
            u"Garis hidup Anda dalam dan jelas, dan bertepatan dengan titik awal dari garis kebijaksanaan. Semua ini menunjukkan bahwa Anda memiliki kondisi tubuh yang sehat. Anda adalah orang yang sangat  berhati-hati, sangat mencintai keluarga, tetapi Anda juga perlu berbagi dengan keluarga dan teman-teman Anda tentang perasaan hati Anda.",
            u"Garis hidup Anda halus dan mulus, Anda harus mulai berolahraga, jaga kesehatan tubuh.   Anda adalah orang yang sangat berhati-hati dan inisiatif untuk berinteraksi dengan orang lain .",
            u"Garis hidup Anda halus dan mulus, dan Anda harus memperhatikan olahraga dan menjaga kebugaran Anda. Anda adalah orang yang sangat berhati-hati, sangat mencintai keluarga, tetapi Anda juga perlu berbagi dengan keluarga dan teman-teman Anda tentang perasaan hati Anda.",
            u"Garis hidup Anda dalam dan jelas, dan bertepatan dengan titik awal dari garis kebijaksanaan. Semua ini menunjukkan bahwa Anda memiliki kondisi tubuh yang sehat.  Anda adalah pribadi yang mandiri dan berani mengambil risiko, sangat mencintai keluarga, memiliki inisatif untuk berinteraksi dengan orang lain.",
            u"Garis hidup Anda dalam dan jelas, dan bertepatan dengan titik awal dari garis kebijaksanaan. Semua ini menunjukkan bahwa Anda memiliki kondisi tubuh yang sehat.  Anda adalah pribadi yang mandiri dan berani mengambil risiko, sangat mencintai keluarga, tetapi Anda juga perlu berbagi dengan keluarga dan teman-teman Anda tentang perasaan hati Anda.",
            u"Garis hidup Anda halus dan mulus, dan Anda harus mulai berolahraga dan menjaga kebugaran Anda. Anda adalah pribadi yang mandiri dan berani mengambil risiko, sangat mencintai keluarga, memiliki inisatif untuk berinteraksi dengan orang lain.",
            u"Garis hidup Anda halus dan mulus, dan Anda harus mulai berolahraga dan menjaga kebugaran Anda. Anda adalah pribadi yang mandiri dan berani mengambil risiko, sangat mencintai keluarga, tetapi Anda juga perlu berbagi dengan keluarga dan teman-teman Anda tentang perasaan hati Anda."
        ],
        wisdom: [
            u"Garis kebijaksanaan Anda dalam dan jelas, yang menunjukkan bahwa Anda adalah seorang yang fleksibel. TBukan hanya pola pikir Anda gesit, cara Anda dalam berpikir juga sangat menggunakan logika, dan keputusan yang Anda buat  rasional dan benar, dengan pemahaman yang sangat baik dan kemampuan  berkonsentrasi Anda mampu untuk fokus  pada pekerjaan Anda untuk waktu yang lama, Ketika melakukan sesuatu Anda akan berdasarkan realita yang ada, dan tujuan Anda jelas. Anda dapat mengembangkan bakat Anda pada bidang tertentu.",
            u"Garis kebijaksanaan Anda dalam dan jelas, yang menunjukkan bahwa Anda adalah seorang pemikir yang fleksibel. Tidak hanya pikiran Anda gesit, asosiasi faktual sangat logis, dan keputusan yang Anda buat lebih rasional dan benar, dengan pemahaman yang sangat baik dan kemampuan untuk berkonsentrasi pada pekerjaan Anda untuk waktu yang lama.  Pekerjaan akan didasarkan pada situasi aktual, tujuannya jelas, dan Anda dapat sepenuhnya menyadari potensi Anda di bidang tertentu.",
            u"Garis kebijaksanaan Anda halus dan mulus, yang menunjukkan bahwa Anda adalah orang yang lebih memainkan perasaan, memperhatikan komunikasi dalam hubungan, kaya akan imajinasi, kemampuan beradaptasi yang kuat, seperti perubahan, suka bertanya, dan memiliki  ketertarikan terhadap banyak hal tetapi juga memperhatikan rencana awal Anda.",
            u"Garis kebijaksanaan Anda halus dan halus, yang menunjukkan bahwa Anda adalah orang yang sentimental, memperhatikan komunikasi emosional, dan memiliki imajinasi yang sangat kaya.Pekerjaan akan didasarkan pada situasi aktual, tujuannya jelas, dan Anda dapat sepenuhnya menyadari potensi Anda di bidang tertentu.",
        ],
        emotion: [
            u"Garis percintaan Anda sangat jelas, menunjukkan bahwa Anda adalah orang yang percaya diri, dan  Anda adalah seseorang yang hangat dan murah hati, memiliki prinsip sendiri dalam hubungan , lebih suka memimpin, dan biasanya yang mengambil langkah pertama duluan dalam hubungan. Ramah,penuh energi, dan orang yang ceria adalah kriteria yang Anda butuhkan pada saat mencari pasangan.",
            u"Garis percintaan Anda sangat jelas, menunjukkan bahwa Anda percaya diri pada emosi Anda dan hangat dan murah hati kepada orang-orang.  Bicara soal perasaan, Mata Anda tajam dan cerdas, dan Anda tidak terlalu bersemangat untuk jatuh cinta. Akan ada lebih banyak mempertimbangkan banyak hal dan cenderung pasif, Anda ingin berkembang secara pelan-pelan dari sahabat menjadi cinta.",
            u"Garis percintaan Anda halus dan mulus. Anda mungkin menghadapi masalah dalam hubungan atau merasa tidak bahagia.   Hubungan dapat hancur dengan mudah karena perasaan yang tidak pasti dan tidak nyaman. Anda ingin terus mencari jaminan dari pasangan Anda.   Pada saat yang sama,Anda memiliki prinsip sendiri suka memimpin. Dalam hubungan biasanya Anda adalah orang yang mengambil langkah pertama.  Ramah. penuuh  energi, dan  ceria adalah kriteria yang Anda butuhkan pada saat mencari pasangan.",
            u"Garis percintaan Anda halus dan mulus. Anda mungkin menghadapi masalah dalam hubungan atau merasa tidak bahagia.   Hubungan dapat hancur dengan mudah karena perasaan yang tidak pasti dan tidak nyaman. Anda ingin terus mencari jaminan dari pasangan Anda.   Pada saat yang sama,Anda memiliki prinsip sendiri suka memimpin. Dalam hubungan biasanya Anda adalah orang yang mengambil langkah pertama, Anda ingin mencari hubungan yang berkembang secara pelan-pelan dari sahabat menjadi cinta.",
            ],
        fate: [
            u"Garis nasib Anda sangat jelas, menunjukkan bahwa Anda adalah pribadi yang sangat kuat , memiliki wawasan luas,dan Anda adalah orang yang dapat dipercaya, memiliki sikap sebagai pemimpin, melakukan segala sesuatu dengan serius , dan dapat mengendalikan nasib Anda sendiri.",
            u"Garis nasib Anda tidak terlalu jelas, menunjukkan bahwa kehidupan memberi Anda banyak gejolak, perubahan lingkungan membuat Anda mengalami kesulitan, Anda tidak ingin terikat oleh tradisi, Anda akan hidup sesuai dengan aturan Anda sendiri.  Selama Anda terus melakukan sesuatu sesuai dengan yang Anda mau, hidup Anda akan sangat istimewa dan berbeda dengan orang lain.",
            ],
        solar: [
            u"Garis matahari Anda dalam dan jelas, menunjukkan bahwa Anda memiliki kepribadian yang menarik, sifat Anda hangat seperti sinar matahari, optimis dan ramah, dan bakat bawaan, dengan waktu dan kesempatan yang tepat,  Anda bisa memperoleh  kesuksesan besar dalam hidup.",
            u"Garis surya Anda tidak terlalu jelas, menunjukkan bahwa situasi yang ada membuat Anda tidak puas. Berbicara soal kebahagiaan, meskipun belum tiba, selama Anda yakin, Anda pasti akan berhasil.",
        ]
    },
}

class PalmService(object):
    '''
    结果生成逻辑 https://shimo.im/mindmaps/NGIxXtpddR8F6eOb/
    代码: https://github.com/xuqingwenkk/palmprint_classification/tree/master/pyboostcvconverter
    '''
    ORDER = [palm_type, life, wisdom, emotion, fate, solar]
    @classmethod
    def bools_2_int(cls, bool_lst):
        res = 0
        for _ in bool_lst:
            res += int(_)
            res *= 2
        res/=2
        return res

    @classmethod
    def times_left(cls, user_id):
        total_times = 10
        if setting.IS_DEV:
            total_times = 1000
        used = PalmResult.objects(user_id=user_id, create_time__gt=(datetime.datetime.now() - datetime.timedelta(days=1))).counts()
        return total_times - used


    @classmethod
    def get_type(cls, is_palm_rectangle, shorter_finger):
        if not is_palm_rectangle:
            if shorter_finger:
                return 0
            return 1
        if shorter_finger:
            return 2
        return 3

    @classmethod
    def get_life(cls, life_obvious, life_long, fate_wisdom_not_together):
        if not fate_wisdom_not_together:   # 生命线与智慧线起点重合
            if life_obvious:
                if life_long:
                    return 0
                return 1
            if life_long:
                if life_long:
                    return 2
                return 3
        return 0

    @classmethod
    def get_wisdom(cls, wisdom_obvious, wisdom_long):
        return 0

    @classmethod
    def get_emotion(cls, emotion_obvious, emotion_wind):
        return 0

    @classmethod
    def get_fate(cls, fate_obvious):
        return 0

    @classmethod
    def get_solar(cls, solar_obvious):
        return 0

    @classmethod
    def output_res(cls, pic):
        if cls.times_left(request.user_id) < 1:
            return u'you have run out of opportunity, please retry one day latter ~', False
        user_id = request.user_id
        if not user_id or not TokenBucketService.get_token('palm_limit' + user_id, 1, 1000, 1000):
            return u'Your palmitry test oppurtunity has run out today, you can try it tomorrow ~', False
        img = AliOssService.get_binary_from_bucket(pic)
        if not img:
            return u'picture not exists', False
        f_name = '/tmp/%s' % pic
        with open(f_name, 'w') as f:
            f.write(img)
            f.close()
        img = cv2.imread(f_name)
        res = pbcvt.OutputFate(img)
        res = res[:11]
        for el in res:
            print el
        for _ in res:
            if _ not in [0, 1]:
                return u'what you upload is not a palm, please retry', False
        shorter_finger, is_palm_rectangle, solar_obvious, wisdom_obvious, wisdom_long, emotion_obvious, emotion_wind, \
        life_obvious, life_long, fate_obvious, fate_wisdom_not_together = tuple([True if el == 0 else False for el in res])
        # palm_type_ind = cls.get_type(is_palm_rectangle, shorter_finger)
        # life_ind = cls.get_life(life_obvious, life_long, fate_wisdom_not_together)
        # wisdom_ind = cls.get_wisdom(wisdom_obvious, wisdom_long)
        # emotion_ind = cls.get_emotion(emotion_obvious, emotion_wind)
        # fate_ind = cls.get_fate(fate_obvious)
        # solar_ind = cls.get_solar(solar_obvious)
        palm_type_ind = cls.bools_2_int([is_palm_rectangle, not shorter_finger])
        life_ind = cls.bools_2_int([fate_wisdom_not_together, not life_obvious, not life_long])
        wisdom_ind = cls.bools_2_int([not wisdom_obvious, not wisdom_long])
        emotion_ind = cls.bools_2_int([not emotion_obvious, not emotion_wind])
        fate_ind = cls.bools_2_int([not fate_obvious])
        solar_ind = cls.bools_2_int([not solar_obvious])
        res = cls.get_res_by_inds(palm_type_ind, life_ind, wisdom_ind, emotion_ind, fate_ind, solar_ind)
        palm_id = PalmResult.create(res, user_id)
        res.update({'result_id': palm_id})
        return res, True

    @classmethod
    def get_res_by_inds(cls, palm_type_ind, life_ind, wisdom_ind, emotion_ind, fate_ind, solar_ind):
        def get_desc(raw_m, key, ind):
            lst = raw_m.get(key)
            if len(lst) > ind:
                return lst[ind]
            return u'not set yet'
        region = GlobalizationService.get_region()
        raw_m = desc.get(region, {})
        res = {
            palm_type: get_desc(raw_m, palm_type, palm_type_ind),
            life: get_desc(raw_m, life, life_ind),
            wisdom: get_desc(raw_m, wisdom, wisdom_ind),
            emotion: get_desc(raw_m, emotion, emotion_ind),
            fate: get_desc(raw_m, fate, fate_ind),
            solar: get_desc(raw_m, solar, solar_ind)
        }
        return res

    @classmethod
    def get_res_by_result_id(cls, result_id):
        return PalmResult.get_by_id(result_id)

