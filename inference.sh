## VOC
# DATA_ROOT=/home/yb/dataset/VOC/PascalVOC12/VOCdevkit/VOC2012
# DATASET=voc
# TASK=15-5
# EPOCH=30
# BATCH=4
# VAL_BATCH=4
# LOSS=bce_loss
# KD_LOSS=KD_loss
# LR=0.01
# THRESH=0.7
# MEMORY=0
# CKPT=checkpoints/

# python eval.py --data_root ${DATA_ROOT} --model deeplabv3_resnet101 --gpu_id 3 --crop_val --lr ${LR} \
#     --batch_size ${BATCH} --val_batch_size ${VAL_BATCH} --train_epoch ${EPOCH}  --loss_type ${LOSS} --KD_loss_type ${KD_LOSS} --use_KD_layer_weight\
#     --dataset ${DATASET} --task ${TASK} --overlap --lr_policy poly \
#     --pseudo --pseudo_thresh ${THRESH} --freeze  --bn_freeze  \
#     --unknown --w_transfer --amp --mem_size ${MEMORY}



## ADE
# DATA_ROOT=/home/yb/dataset/ADEChallengeData2016/
# DATASET=ade
# TASK=100-10 # [100-5, 100-10, 100-50, 50-50]
# EPOCH=30
# BATCH=1
# VAL_BATCH=1
# LOSS=bce_loss
# KD_LOSS=KD_loss
# LR=0.01
# THRESH=0.7
# MEMORY=0
# CKPT=checkpoints/deeplabv3_resnet101_ade_100-10_step_5_overlap.pth

# python eval.py --data_root ${DATA_ROOT} --model deeplabv3_resnet101 --gpu_id 3 --crop_val --lr ${LR} \
#     --batch_size ${BATCH} --val_batch_size ${VAL_BATCH} --train_epoch ${EPOCH}  --loss_type ${LOSS} --KD_loss_type ${KD_LOSS} --use_KD_layer_weight\
#     --dataset ${DATASET} --task ${TASK} --overlap --lr_policy poly \
#     --pseudo --pseudo_thresh ${THRESH} --freeze  --bn_freeze  \
#     --unknown --w_transfer --amp --mem_size ${MEMORY}


# ISPRS
DATA_ROOT=/home/yb/dataset/ISPRS_2D/postdam/Incremental_RGB_600
DATASET=ISPRS
TASK=2-2-1 #[4-1, 2-3, 2-1, 2-2-1]
EPOCH=30
BATCH=4
VAL_BATCH=1
LOSS=bce_loss
KD_LOSS=KD_loss
LR=0.01
THRESH=0.7
CKPT=checkpoints/

python eval.py --data_root ${DATA_ROOT} --model deeplabv3_resnet101 --gpu_id 1 --lr ${LR} \
    --batch_size ${BATCH} --val_batch_size ${VAL_BATCH} --train_epoch ${EPOCH}  --loss_type ${LOSS} --KD_loss_type ${KD_LOSS} --use_KD_layer_weight\
    --dataset ${DATASET} --task ${TASK} --overlap --lr_policy step \
    --pseudo --pseudo_thresh ${THRESH} --freeze  --bn_freeze  \
    --unknown --w_transfer --amp 